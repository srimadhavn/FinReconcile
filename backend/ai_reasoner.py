import os
import json
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

from matcher_fuzzy import run_fuzzy_matching, string_similarity, date_diff_days
from gemini_client import analyze_exception_with_gemini, reset_run_enrich_counter

# Standard Finance Exception Taxonomy
TAXONOMY_CATEGORIES = [
    "DUPLICATE_ENTRY",
    "MISSING_IN_BANK",
    "MISSING_IN_LEDGER",
    "MISSING_IN_GATEWAY",
    "FEE_DEDUCTION_MISMATCH",
    "TIMING_LAG_EXCEEDED",
    "REFERENCE_MISMATCH",
    "UNEXPLAINABLE_ANOMALY"
]

def analyze_exception_deterministic(
    record_type: str,
    record: Dict[str, Any],
    all_unmatched_ledger: List[Dict[str, Any]],
    all_unmatched_bank: List[Dict[str, Any]],
    all_unmatched_gateway: List[Dict[str, Any]],
    matched_groups: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Intelligent financial rule engine that synthesizes multi-source context
    and generates structured audit logs adhering to the finance taxonomy.
    """
    if record_type == "ledger":
        txn_id = record.get("txn_id", "")
        amount = float(record.get("amount", 0.0))
        date = record.get("date", "")
        ref = record.get("reference", "")
        cp = record.get("counterparty", "")
        
        # 1. Check for Duplicate Entry in Ledger
        dup_ledger = [l for l in all_unmatched_ledger if l["txn_id"] != txn_id and abs(float(l["amount"]) - amount) < 0.01 and l.get("reference") == ref]
        if not dup_ledger:
            # Check if this txn matches an already matched transaction
            for m in matched_groups:
                if m.get("ledger") and m["ledger"]["reference"] == ref and abs(float(m["ledger"]["amount"]) - amount) < 0.01:
                    dup_ledger.append(m["ledger"])
                    break
                    
        if dup_ledger:
            other_id = dup_ledger[0]["txn_id"]
            return {
                "category": "DUPLICATE_ENTRY",
                "plain_english_explanation": f"Duplicate ledger entry detected for reference '{ref}' with identical amount INR {amount:,.2f}.",
                "cited_fields": f"Ledger.txn_id ({txn_id}) vs Ledger.txn_id ({other_id}) [amount: {amount}, reference: {ref}]",
                "ai_confidence": 0.96,
                "remediation_suggestion": f"Void duplicate voucher '{txn_id}' in ERP to prevent double booking.",
                "root_cause": "System double-posting during batch sync."
            }
            
        # 2. Check for Severe Amount Anomaly with existing Bank transaction
        for b in all_unmatched_bank:
            b_narration = b.get("narration", "")
            if ref in b_narration or cp[:5].upper() in b_narration.upper():
                b_amt = float(b.get("amount", 0.0))
                diff = abs(amount - b_amt)
                if diff > 500.0:
                    return {
                        "category": "UNEXPLAINABLE_ANOMALY",
                        "plain_english_explanation": f"Disputed amount mismatch of INR {diff:,.2f} with Bank narration '{b_narration[:40]}...'. Marked for manual review.",
                        "cited_fields": f"Ledger.amount (INR {amount:,.2f}) vs Bank.amount (INR {b_amt:,.2f}), Narration: '{b_narration}'",
                        "ai_confidence": 0.91,
                        "remediation_suggestion": "Escalate to Treasury Ops for chargeback / partial settlement investigation.",
                        "root_cause": "Possible dispute, chargeback hold, or unapproved deduction."
                    }
                    
        # 3. Check for Gateway match but missing in Bank
        gw_matches = [g for g in all_unmatched_gateway if g.get("order_ref") == ref or abs(float(g.get("settled_amount", 0)) - amount) < 10.0]
        if gw_matches:
            gw = gw_matches[0]
            return {
                "category": "MISSING_IN_BANK",
                "plain_english_explanation": f"Present in Ledger and Gateway ({gw['payment_id']}) for INR {amount:,.2f}, but missing from Bank Statement.",
                "cited_fields": f"Ledger.txn_id ({txn_id}) & Gateway.payment_id ({gw['payment_id']}) vs Bank Statement (NO_MATCH)",
                "ai_confidence": 0.94,
                "remediation_suggestion": "Verify gateway payout batch transfer status with bank partner.",
                "root_cause": "Gateway batch payout settlement dropped or pending bank processing."
            }
            
        # 4. Pure Missing in Bank & Gateway
        return {
            "category": "MISSING_IN_BANK",
            "plain_english_explanation": f"Transaction recorded in internal Ledger for {cp} (INR {amount:,.2f}), but no corresponding bank or gateway record exists.",
            "cited_fields": f"Ledger.txn_id ({txn_id}) [Date: {date}, Ref: {ref}]",
            "ai_confidence": 0.89,
            "remediation_suggestion": "Confirm whether payment failed or invoice was recorded prematurely.",
            "root_cause": "Unexecuted payment or cancelled checkout order."
        }

    elif record_type == "bank":
        b_id = record.get("bank_txn_id", "")
        amount = float(record.get("amount", 0.0))
        date = record.get("date", "")
        narration = record.get("narration", "")
        
        # Check for unrecorded direct credit
        return {
            "category": "MISSING_IN_LEDGER",
            "plain_english_explanation": f"Direct bank credit of INR {amount:,.2f} received with narration '{narration}' has no matching Ledger voucher.",
            "cited_fields": f"Bank.bank_txn_id ({b_id}) [Date: {date}, Amount: {amount}] vs Ledger (NO_RECORD)",
            "ai_confidence": 0.92,
            "remediation_suggestion": "Create journal voucher in Ledger and map to corresponding customer account.",
            "root_cause": "Direct wire transfer / NEFT inward credit without invoice reference."
        }
        
    elif record_type == "gateway":
        g_id = record.get("payment_id", "")
        amount = float(record.get("settled_amount", 0.0))
        date = record.get("settlement_date", "")
        ref = record.get("order_ref", "")
        fee = record.get("fee", 0.0)
        
        return {
            "category": "MISSING_IN_LEDGER",
            "plain_english_explanation": f"Gateway settlement {g_id} for order '{ref}' (Net: INR {amount:,.2f}, Fee: INR {fee}) is unlinked in Ledger.",
            "cited_fields": f"Gateway.payment_id ({g_id}) vs Ledger (NO_RECORD)",
            "ai_confidence": 0.88,
            "remediation_suggestion": "Re-sync gateway webhook to post settlement voucher in ERP.",
            "root_cause": "Webhook delivery failure or delayed ERP ingestion."
        }
        
    return {
        "category": "UNEXPLAINABLE_ANOMALY",
        "plain_english_explanation": "Unresolved discrepancy across sources requiring manual human controller audit.",
        "cited_fields": "All sources (Inconclusive)",
        "ai_confidence": 0.65,
        "remediation_suggestion": "Manual investigation by Senior Controller.",
        "root_cause": "Data mismatch beyond tolerance limits."
    }

async def call_claude_or_llm(prompt: str) -> Optional[str]:
    """Optional LLM API caller if ANTHROPIC_API_KEY / OPENAI_API_KEY is in environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                if res.status_code == 200:
                    data = res.json()
                    return data["content"][0]["text"]
        except Exception:
            pass
    return None

def run_ai_reasoning_pipeline(
    dataset: Dict[str, Any],
    date_tolerance_days: int = 3,
    fee_tolerance_pct: float = 0.035
) -> Dict[str, Any]:
    """
    Phase 3: AI Exception Reasoning Layer.
    Takes the fuzzy matching results and unresolved items, performs deep cross-source
    auditing, classifies each exception into standard taxonomy, and constructs an
    auditable plain-English reasoning trail with cited fields.
    """
    fuzzy_result = run_fuzzy_matching(
        dataset, 
        date_tolerance_days=date_tolerance_days, 
        fee_tolerance_pct=fee_tolerance_pct
    )
    
    matched_groups = fuzzy_result["matched_groups"]
    unmatched = fuzzy_result["unmatched"]
    
    unmatched_ledger = unmatched.get("ledger", [])
    unmatched_bank = unmatched.get("bank", [])
    unmatched_gateway = unmatched.get("gateway", [])
    
    exceptions_list: List[Dict[str, Any]] = []
    seen_exception_signatures = set()
    reset_run_enrich_counter()
    
    # Process Ledger Unmatched
    for ldg in unmatched_ledger:
        det = analyze_exception_deterministic(
            "ledger", ldg, unmatched_ledger, unmatched_bank, unmatched_gateway, matched_groups
        )
        analysis = analyze_exception_with_gemini("ledger", ldg, det)
        exc_id = f"EXC-LDG-{len(exceptions_list)+1:03d}"
        exceptions_list.append({
            "id": exc_id,
            "source": "Ledger",
            "source_record_id": ldg["txn_id"],
            "amount": ldg["amount"],
            "date": ldg["date"],
            "reference": ldg.get("reference", ""),
            "counterparty": ldg.get("counterparty", "Unknown"),
            "category": analysis["category"],
            "ai_confidence": analysis["ai_confidence"],
            "plain_english_explanation": analysis["plain_english_explanation"],
            "cited_fields": analysis["cited_fields"],
            "root_cause": analysis.get("root_cause", det.get("root_cause", "")),
            "remediation_suggestion": analysis["remediation_suggestion"],
            "llm_engine": analysis.get("llm_engine", "Deterministic AI Rule Reasoner"),
            "status": "UNRESOLVED",
            "guardrail_flag": "STRICT_UNRESOLVED (Not force-matched to protect audit integrity)",
            "raw_record": ldg
        })

    # Process Bank Unmatched
    for b in unmatched_bank:
        sig = f"BANK_{b['bank_txn_id']}"
        if sig in seen_exception_signatures:
            continue
        seen_exception_signatures.add(sig)

        det = analyze_exception_deterministic(
            "bank", b, unmatched_ledger, unmatched_bank, unmatched_gateway, matched_groups
        )
        analysis = analyze_exception_with_gemini("bank", b, det)
        exc_id = f"EXC-BNK-{len(exceptions_list)+1:03d}"
        exceptions_list.append({
            "id": exc_id,
            "source": "Bank Statement",
            "source_record_id": b["bank_txn_id"],
            "amount": b["amount"],
            "date": b["date"],
            "reference": b.get("utr_reference", ""),
            "counterparty": b.get("narration", "").split("/")[0] if "/" in b.get("narration", "") else "Bank Inward",
            "category": analysis["category"],
            "ai_confidence": analysis["ai_confidence"],
            "plain_english_explanation": analysis["plain_english_explanation"],
            "cited_fields": analysis["cited_fields"],
            "root_cause": analysis.get("root_cause", det.get("root_cause", "")),
            "remediation_suggestion": analysis["remediation_suggestion"],
            "llm_engine": analysis.get("llm_engine", "Deterministic AI Rule Reasoner"),
            "status": "UNRESOLVED",
            "guardrail_flag": "STRICT_UNRESOLVED (Not force-matched to protect audit integrity)",
            "raw_record": b
        })

    # Process Gateway Unmatched
    for g in unmatched_gateway:
        sig = f"GW_{g['payment_id']}"
        if sig in seen_exception_signatures:
            continue
        seen_exception_signatures.add(sig)

        det = analyze_exception_deterministic(
            "gateway", g, unmatched_ledger, unmatched_bank, unmatched_gateway, matched_groups
        )
        analysis = analyze_exception_with_gemini("gateway", g, det)
        exc_id = f"EXC-GW-{len(exceptions_list)+1:03d}"
        exceptions_list.append({
            "id": exc_id,
            "source": "Gateway Settlement",
            "source_record_id": g["payment_id"],
            "amount": g["settled_amount"],
            "date": g["settlement_date"],
            "reference": g.get("order_ref", ""),
            "counterparty": "Gateway Merchant Settlement",
            "category": analysis["category"],
            "ai_confidence": analysis["ai_confidence"],
            "plain_english_explanation": analysis["plain_english_explanation"],
            "cited_fields": analysis["cited_fields"],
            "root_cause": analysis.get("root_cause", det.get("root_cause", "")),
            "remediation_suggestion": analysis["remediation_suggestion"],
            "llm_engine": analysis.get("llm_engine", "Deterministic AI Rule Reasoner"),
            "status": "UNRESOLVED",
            "guardrail_flag": "STRICT_UNRESOLVED (Not force-matched to protect audit integrity)",
            "raw_record": g
        })
        
    # Taxonomy counts
    tax_counts: Dict[str, int] = {}
    for exc in exceptions_list:
        cat = exc["category"]
        tax_counts[cat] = tax_counts.get(cat, 0) + 1
        
    summary = fuzzy_result["summary"]
    total_base = summary["total_base_records"]
    total_matched = len(matched_groups)
    
    # Calculate average confidence
    all_confs = [m["confidence_score"] for m in matched_groups] + [e["ai_confidence"] for e in exceptions_list]
    avg_conf = round(sum(all_confs) / max(len(all_confs), 1), 3)
    
    return {
        "phase": 3,
        "engine": "AI Exception Reasoning & Audit Layer",
        "thresholds_disclosed": fuzzy_result["thresholds_disclosed"],
        "summary": {
            "total_base_records": total_base,
            "total_matched": total_matched,
            "match_rate_percentage": summary["match_rate_percentage"],
            "exact_matches": summary["confidence_breakdown"].get("Exact", 0),
            "fuzzy_matches": summary["confidence_breakdown"].get("High", 0) + summary["confidence_breakdown"].get("Medium", 0),
            "total_exceptions": len(exceptions_list),
            "average_confidence": avg_conf,
            "confidence_breakdown": summary["confidence_breakdown"],
            "exception_taxonomy": tax_counts
        },
        "matched_records": matched_groups,
        "exceptions": exceptions_list,
        "unmatched_raw": unmatched
    }

if __name__ == "__main__":
    from generate_synthetic_data import generate_synthetic_data
    dataset = generate_synthetic_data(seed=42, count=60)
    result = run_ai_reasoning_pipeline(dataset)
    print(json.dumps(result["summary"], indent=2))

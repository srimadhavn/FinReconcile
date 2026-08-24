import difflib
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

def parse_date(d_str: str) -> datetime:
    try:
        return datetime.strptime(d_str, "%Y-%m-%d")
    except Exception:
        return datetime.now()

def date_diff_days(d1_str: str, d2_str: str) -> int:
    try:
        dt1 = parse_date(d1_str)
        dt2 = parse_date(d2_str)
        return abs((dt1 - dt2).days)
    except Exception:
        return 999

def string_similarity(s1: str, s2: str) -> float:
    """Computes normalized fuzzy similarity between two strings."""
    s1_clean = s1.upper().replace("-", " ").replace("/", " ").replace("_", " ").strip()
    s2_clean = s2.upper().replace("-", " ").replace("/", " ").replace("_", " ").strip()
    
    # Check token overlap
    tokens1 = set(s1_clean.split())
    tokens2 = set(s2_clean.split())
    if tokens1 and tokens2:
        overlap = len(tokens1.intersection(tokens2)) / max(len(tokens1), len(tokens2))
        if overlap > 0.5:
            return 0.7 + 0.3 * overlap
            
    # Sequence matcher ratio
    seq_ratio = difflib.SequenceMatcher(None, s1_clean, s2_clean).ratio()
    return seq_ratio

def is_amount_compatible(
    ledger_amt: float, 
    candidate_amt: float, 
    fee_tolerance_pct: float = 0.035, 
    fixed_tolerance: float = 100.0
) -> Tuple[bool, float, str]:
    """
    Checks if candidate amount is compatible with ledger amount.
    Returns: (is_compatible, amount_score, reason)
    """
    diff = abs(ledger_amt - candidate_amt)
    if diff < 0.01:
        return True, 1.0, "Exact amount"
        
    # Gateway fee deduction scenario: Candidate is net settled (less than ledger)
    if candidate_amt < ledger_amt:
        deduction = ledger_amt - candidate_amt
        deduction_pct = deduction / ledger_amt
        if deduction_pct <= fee_tolerance_pct or deduction <= fixed_tolerance:
            # High plausibility of standard 1.5% - 2.5% MDR fee
            fee_score = max(0.70, 1.0 - (deduction_pct * 5.0))
            return True, fee_score, f"Fee/Rounding deduction: INR {deduction:.2f} ({deduction_pct*100:.2f}%)"
            
    # Minor FX / penny rounding
    if diff <= 2.0:
        return True, 0.95, f"Penny/Rounding difference of INR {diff:.2f}"
        
    return False, 0.0, f"Incompatible amount diff: INR {diff:.2f}"

def calculate_match_confidence(
    amt_score: float, 
    date_diff: int, 
    max_days: int, 
    ref_sim: float
) -> Tuple[float, str]:
    """
    Calculates combined weighted confidence score:
    - Amount score: 45% weight
    - Date proximity: 25% weight
    - Reference similarity: 30% weight
    """
    date_score = max(0.0, 1.0 - (date_diff / max(max_days + 1, 1)))
    combined = (amt_score * 0.45) + (date_score * 0.25) + (ref_sim * 0.30)
    
    score = round(combined, 3)
    if score >= 0.98:
        tier = "Exact"
    elif score >= 0.82:
        tier = "High"
    elif score >= 0.65:
        tier = "Medium"
    else:
        tier = "Low"
        
    return score, tier

def run_fuzzy_matching(
    dataset: Dict[str, Any],
    date_tolerance_days: int = 3,
    fee_tolerance_pct: float = 0.035,
    min_similarity: float = 0.50
) -> Dict[str, Any]:
    """
    Phase 2: Fuzzy Matching & Confidence Scoring Engine.
    Employs multi-dimensional tolerance windows:
      - Date lag window (T±3 days default)
      - Net gateway fee tolerance (up to 3.5% + ₹100)
      - Fuzzy narration & reference matching (token + sequence ratio)
    """
    ledger_records = list(dataset.get("ledger", []))
    bank_records = list(dataset.get("bank", []))
    gateway_records = list(dataset.get("gateway", []))
    
    total_ledger = len(ledger_records)
    total_bank = len(bank_records)
    total_gateway = len(gateway_records)
    total_base_records = max(total_ledger, total_bank, total_gateway)
    
    used_ledger_ids = set()
    used_bank_ids = set()
    used_gateway_ids = set()
    
    matched_groups: List[Dict[str, Any]] = []
    
    # -------------------------------------------------------------
    # Step 1: Deterministic Exact Pass (Score = 1.0)
    # -------------------------------------------------------------
    for ldg in ledger_records:
        ldg_amt = float(ldg["amount"])
        ldg_date = str(ldg["date"])
        ldg_ref = str(ldg["reference"]).strip().upper()
        
        # Look for exact bank match
        matching_b = None
        for b in bank_records:
            if b["bank_txn_id"] in used_bank_ids:
                continue
            if abs(float(b["amount"]) - ldg_amt) < 0.01 and str(b["date"]) == ldg_date:
                if ldg_ref in b["narration"].upper():
                    matching_b = b
                    break
                    
        # Look for exact gateway match
        matching_g = None
        for g in gateway_records:
            if g["payment_id"] in used_gateway_ids:
                continue
            if abs(float(g.get("settled_amount", g.get("amount", 0))) - ldg_amt) < 0.01 and str(g.get("settlement_date", g.get("date", ""))) == ldg_date:
                g_ref = str(g.get("order_ref", g.get("reference", g.get("payment_id", "")))).strip().upper()
                if g_ref == ldg_ref or ldg_ref in g_ref or g_ref in ldg_ref:
                    matching_g = g
                    break
                    
        if matching_b and matching_g:
            used_ledger_ids.add(ldg["txn_id"])
            used_bank_ids.add(matching_b["bank_txn_id"])
            used_gateway_ids.add(matching_g["payment_id"])
            
            matched_groups.append({
                "match_id": f"MATCH-P2-{len(matched_groups)+1:03d}",
                "match_type": "EXACT_3WAY",
                "confidence_score": 1.0,
                "confidence_tier": "Exact",
                "status": "MATCHED",
                "ledger": ldg,
                "bank": matching_b,
                "gateway": matching_g,
                "discrepancies": [],
                "reasoning": "Exact 3-way match across amount, date, and reference."
            })

    # -------------------------------------------------------------
    # Step 2: Multi-Source Fuzzy & Tolerance Pass for Remaining Records
    # -------------------------------------------------------------
    for ldg in ledger_records:
        if ldg["txn_id"] in used_ledger_ids:
            continue
            
        ldg_amt = float(ldg["amount"])
        ldg_date = str(ldg["date"])
        ldg_ref = str(ldg["reference"]).strip()
        ldg_cp = str(ldg.get("counterparty", "")).strip()
        
        best_b = None
        best_b_score = 0.0
        best_b_details = {}
        
        # Search candidate Bank records
        for b in bank_records:
            if b["bank_txn_id"] in used_bank_ids:
                continue
                
            b_amt = float(b["amount"])
            b_date = str(b["date"])
            d_diff = date_diff_days(ldg_date, b_date)
            
            if d_diff > date_tolerance_days:
                continue
                
            amt_ok, amt_sc, amt_msg = is_amount_compatible(
                ldg_amt, b_amt, fee_tolerance_pct=fee_tolerance_pct
            )
            if not amt_ok:
                continue
                
            # Compute string similarity against narration
            ref_sim = max(
                string_similarity(ldg_ref, b["narration"]),
                string_similarity(ldg_cp, b["narration"])
            )
            
            # Check if reference numbers overlap (e.g. 1042)
            ref_num = "".join(filter(str.isdigit, ldg_ref))
            if ref_num and ref_num in b["narration"]:
                ref_sim = max(ref_sim, 0.85)
                
            if ref_sim < min_similarity:
                continue
                
            conf, tier = calculate_match_confidence(amt_sc, d_diff, date_tolerance_days, ref_sim)
            if conf > best_b_score and conf >= 0.60:
                best_b_score = conf
                best_b = b
                best_b_details = {
                    "confidence": conf,
                    "tier": tier,
                    "date_diff": d_diff,
                    "amt_msg": amt_msg,
                    "ref_sim": ref_sim
                }
                
        # Search candidate Gateway records
        best_g = None
        best_g_score = 0.0
        best_g_details = {}
        
        for g in gateway_records:
            if g["payment_id"] in used_gateway_ids:
                continue
                
            g_amt = float(g["settled_amount"])
            g_date = str(g["settlement_date"])
            d_diff = date_diff_days(ldg_date, g_date)
            
            if d_diff > date_tolerance_days:
                continue
                
            # Gateway might record gross minus fee
            total_g_val = g_amt + float(g.get("fee", 0.0))
            amt_ok, amt_sc, amt_msg = is_amount_compatible(
                ldg_amt, g_amt, fee_tolerance_pct=fee_tolerance_pct
            )
            if not amt_ok and abs(ldg_amt - total_g_val) < 0.01:
                amt_ok = True
                amt_sc = 0.98
                amt_msg = f"Gross matches (Fee of INR {g.get('fee', 0.0)} accounted)"
                
            if not amt_ok:
                continue
                
            g_ref = str(g.get("order_ref", ""))
            ref_sim = string_similarity(ldg_ref, g_ref)
            ref_num = "".join(filter(str.isdigit, ldg_ref))
            if ref_num and ref_num in g_ref:
                ref_sim = max(ref_sim, 0.90)
                
            if ref_sim < min_similarity:
                continue
                
            conf, tier = calculate_match_confidence(amt_sc, d_diff, date_tolerance_days, ref_sim)
            if conf > best_g_score and conf >= 0.60:
                best_g_score = conf
                best_g = g
                best_g_details = {
                    "confidence": conf,
                    "tier": tier,
                    "date_diff": d_diff,
                    "amt_msg": amt_msg,
                    "ref_sim": ref_sim
                }
                
        # If both bank and gateway matches found with sufficient confidence
        if best_b and best_g:
            used_ledger_ids.add(ldg["txn_id"])
            used_bank_ids.add(best_b["bank_txn_id"])
            used_gateway_ids.add(best_g["payment_id"])
            
            overall_conf = round((best_b_score + best_g_score) / 2.0, 3)
            if overall_conf >= 0.82:
                overall_tier = "High"
            elif overall_conf >= 0.65:
                overall_tier = "Medium"
            else:
                overall_tier = "Low"
                
            discrepancies = []
            if best_b_details.get("date_diff", 0) > 0:
                discrepancies.append(f"Bank date lag: +{best_b_details['date_diff']} day(s)")
            if best_g_details.get("date_diff", 0) > 0:
                discrepancies.append(f"Gateway date lag: +{best_g_details['date_diff']} day(s)")
            if "Fee" in best_b_details.get("amt_msg", "") or "Fee" in best_g_details.get("amt_msg", ""):
                discrepancies.append(f"Gateway fee deducted ({best_g.get('fee', 0.0)})")
            if best_b_details.get("ref_sim", 1.0) < 0.90:
                discrepancies.append("Fuzzy narration string match")
                
            matched_groups.append({
                "match_id": f"MATCH-P2-{len(matched_groups)+1:03d}",
                "match_type": "FUZZY_3WAY",
                "confidence_score": overall_conf,
                "confidence_tier": overall_tier,
                "status": "MATCHED_FUZZY",
                "ledger": ldg,
                "bank": best_b,
                "gateway": best_g,
                "discrepancies": discrepancies,
                "reasoning": f"Fuzzy 3-way match resolved with {overall_tier} confidence ({int(overall_conf*100)}%). Resolved variations: {', '.join(discrepancies) if discrepancies else 'Minor tolerances'}."
            })
            
    # Gather Remaining Unmatched Records
    unmatched_ledger = [l for l in ledger_records if l["txn_id"] not in used_ledger_ids]
    unmatched_bank = [b for b in bank_records if b["bank_txn_id"] not in used_bank_ids]
    unmatched_gateway = [g for g in gateway_records if g["payment_id"] not in used_gateway_ids]
    
    # Calculate Breakdown by Confidence Tier
    conf_breakdown = {"Exact": 0, "High": 0, "Medium": 0, "Low": 0}
    for m in matched_groups:
        tier = m.get("confidence_tier", "Low")
        conf_breakdown[tier] = conf_breakdown.get(tier, 0) + 1
        
    total_matched = len(matched_groups)
    match_rate_pct = round((total_matched / total_base_records) * 100, 2)
    
    return {
        "phase": 2,
        "engine": "Fuzzy Matching & Confidence Scoring Engine",
        "thresholds_disclosed": {
            "date_tolerance_window_days": f"±{date_tolerance_days} days",
            "fee_tolerance_percentage": f"{fee_tolerance_pct*100:.1f}%",
            "min_similarity_threshold": min_similarity,
            "false_match_risk_statement": f"Configured tolerance allows up to T±{date_tolerance_days} settlement lag and up to {fee_tolerance_pct*100:.1f}% MDR fee deductions while guarding against cross-counterparty collisions."
        },
        "summary": {
            "total_base_records": total_base_records,
            "total_matches_found": total_matched,
            "match_rate_percentage": match_rate_pct,
            "confidence_breakdown": conf_breakdown,
            "exception_count": len(unmatched_ledger) + len(unmatched_bank) + len(unmatched_gateway),
            "unmatched_ledger_count": len(unmatched_ledger),
            "unmatched_bank_count": len(unmatched_bank),
            "unmatched_gateway_count": len(unmatched_gateway)
        },
        "matched_groups": matched_groups,
        "unmatched": {
            "ledger": unmatched_ledger,
            "bank": unmatched_bank,
            "gateway": unmatched_gateway
        }
    }

if __name__ == "__main__":
    from generate_synthetic_data import generate_synthetic_data
    dataset = generate_synthetic_data(seed=42, count=60)
    result = run_fuzzy_matching(dataset)
    import json
    print(json.dumps(result["summary"], indent=2))

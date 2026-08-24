import json
from typing import Dict, List, Any, Tuple

def extract_reference_candidate(narration: str) -> str:
    """Helper to extract reference string if present in bank narration."""
    parts = narration.replace("/", " ").replace("-", " ").split()
    for part in parts:
        if part.startswith("ORD") or part.startswith("UTR") or "ORD" in part:
            return part
    return ""

def run_deterministic_matching(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phase 1: Deterministic Exact Matching Engine.
    Matches records strictly when:
      - amount (Ledger) == amount (Bank) == settled_amount (Gateway)
      - date (Ledger) == date (Bank) == settlement_date (Gateway)
      - reference (Ledger) == reference extracted from Bank narration == order_ref (Gateway)
    """
    ledger_records = list(dataset.get("ledger", []))
    bank_records = list(dataset.get("bank", []))
    gateway_records = list(dataset.get("gateway", []))
    
    total_ledger = len(ledger_records)
    total_bank = len(bank_records)
    total_gateway = len(gateway_records)
    
    matched_groups: List[Dict[str, Any]] = []
    
    used_ledger_ids = set()
    used_bank_ids = set()
    used_gateway_ids = set()
    
    # Index Bank records by (amount, date, reference_clean)
    bank_exact_map: Dict[Tuple[float, str, str], List[Dict[str, Any]]] = {}
    for b in bank_records:
        # Check if reference is directly in narration
        narration = b["narration"]
        # Find exact ORD-XXX-XXXX reference token if present
        ref = ""
        for token in narration.split("/"):
            if token.startswith("ORD-"):
                ref = token
                break
        key = (float(b["amount"]), str(b["date"]), ref)
        bank_exact_map.setdefault(key, []).append(b)
        
    # Index Gateway records by (settled_amount, settlement_date, order_ref)
    gateway_exact_map: Dict[Tuple[float, str, str], List[Dict[str, Any]]] = {}
    for g in gateway_records:
        key = (float(g["settled_amount"]), str(g["settlement_date"]), str(g["order_ref"]))
        gateway_exact_map.setdefault(key, []).append(g)

    # Perform Exact 3-Way Join starting from Ledger
    for ldg in ledger_records:
        ldg_id = ldg["txn_id"]
        if ldg_id in used_ledger_ids:
            continue
            
        ldg_amt = float(ldg["amount"])
        ldg_date = str(ldg["date"])
        ldg_ref = str(ldg["reference"])
        
        lookup_key = (ldg_amt, ldg_date, ldg_ref)
        
        b_candidates = bank_exact_map.get(lookup_key, [])
        g_candidates = gateway_exact_map.get(lookup_key, [])
        
        # Find first unused bank and gateway candidate
        selected_b = None
        for b in b_candidates:
            if b["bank_txn_id"] not in used_bank_ids:
                selected_b = b
                break
                
        selected_g = None
        for g in g_candidates:
            if g["payment_id"] not in used_gateway_ids:
                selected_g = g
                break
                
        # Only 3-way exact match if all 3 sources align perfectly
        if selected_b and selected_g:
            used_ledger_ids.add(ldg_id)
            used_bank_ids.add(selected_b["bank_txn_id"])
            used_gateway_ids.add(selected_g["payment_id"])
            
            matched_groups.append({
                "match_id": f"MATCH-EXACT-{len(matched_groups)+1:03d}",
                "match_type": "EXACT_3WAY",
                "confidence_score": 1.0,
                "confidence_tier": "Exact",
                "status": "MATCHED",
                "ledger": ldg,
                "bank": selected_b,
                "gateway": selected_g,
                "discrepancies": [],
                "reasoning": "Exact 3-way match: amount, date, and reference matched across all 3 sources perfectly."
            })
            
    # Gather Unmatched Records
    unmatched_ledger = [l for l in ledger_records if l["txn_id"] not in used_ledger_ids]
    unmatched_bank = [b for b in bank_records if b["bank_txn_id"] not in used_bank_ids]
    unmatched_gateway = [g for g in gateway_records if g["payment_id"] not in used_gateway_ids]
    
    # Calculate Metrics
    # Baseline for 3-way matching is based on ledger ground truth count
    matched_count = len(matched_groups)
    total_reconciliation_base = max(total_ledger, total_bank, total_gateway)
    match_rate_pct = round((matched_count / total_reconciliation_base) * 100, 2)
    
    return {
        "phase": 1,
        "engine": "Deterministic Exact Match Engine",
        "summary": {
            "total_ledger_records": total_ledger,
            "total_bank_records": total_bank,
            "total_gateway_records": total_gateway,
            "total_base_records": total_reconciliation_base,
            "exact_matches_found": matched_count,
            "match_rate_percentage": match_rate_pct,
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
    result = run_deterministic_matching(dataset)
    print(json.dumps(result["summary"], indent=2))

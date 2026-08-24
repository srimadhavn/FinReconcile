from typing import Dict, List, Any
from matcher_fuzzy import run_fuzzy_matching
from ai_reasoner import run_ai_reasoning_pipeline
from evaluator import evaluate_ground_truth_accuracy

def generate_out_of_distribution_batch() -> Dict[str, Any]:
    """
    Hand-crafted Out-Of-Distribution (OOD) stress dataset containing
    subtle edge cases that sit right on the razor edge of tolerance boundaries.
    """
    ledger = []
    bank = []
    gateway = []
    ground_truth = []
    
    # 1. Clean Match (Control)
    ledger.append({
        "txn_id": "TXN-OOD-001",
        "date": "2026-03-10",
        "amount": 15000.0,
        "counterparty": "Acme Global Tech",
        "reference": "ORD-ACME-8001",
        "currency": "INR"
    })
    bank.append({
        "bank_txn_id": "BNK-OOD-8001",
        "date": "2026-03-10",
        "amount": 15000.0,
        "narration": "CMS/NEFT/ORD-ACME-8001/Acme Global Tech/UTR8001",
        "utr_reference": "UTR8001"
    })
    gateway.append({
        "payment_id": "pay_OOD_8001",
        "settled_amount": 15000.0,
        "fee": 0.0,
        "settlement_date": "2026-03-10",
        "order_ref": "ORD-ACME-8001"
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8001",
        "type": "EXACT_MATCH",
        "expected_status": "MATCHED_EXACT",
        "ledger_id": "TXN-OOD-001",
        "bank_id": "BNK-OOD-8001",
        "gateway_id": "pay_OOD_8001"
    })

    # 2. Borderline Fee Discrepancy: Fee deduction of exactly 3.51% (Max tolerance = 3.50%)
    # Gross = 20,000.00 | 3.51% fee = 702.00 | Net = 19,298.00
    # Plausible fee, but sits 0.01% outside threshold -> Guardrail MUST trip & leave as UNRESOLVED
    ledger.append({
        "txn_id": "TXN-OOD-002",
        "date": "2026-03-11",
        "amount": 20000.0,
        "counterparty": "Stripe Billing Solutions",
        "reference": "ORD-STRIPE-8002",
        "currency": "INR"
    })
    bank.append({
        "bank_txn_id": "BNK-OOD-8002",
        "date": "2026-03-11",
        "amount": 19298.0, # 3.51% deduction (Outside 3.5% tolerance)
        "narration": "SETTLEMENT/ORD-STRIPE-8002/Stripe Billing/UTR8002",
        "utr_reference": "UTR8002"
    })
    gateway.append({
        "payment_id": "pay_OOD_8002",
        "settled_amount": 19298.0,
        "fee": 702.0,
        "settlement_date": "2026-03-11",
        "order_ref": "ORD-STRIPE-8002"
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8002",
        "type": "BORDERLINE_FEE_OVERAGE",
        "expected_status": "EXCEPTION", # Expect guardrail rejection
        "ledger_id": "TXN-OOD-002",
        "bank_id": "BNK-OOD-8002",
        "gateway_id": "pay_OOD_8002"
    })

    # 3. Borderline Date Lag Drift: Settlement is T+4 days (Max tolerance = T+3 days)
    ledger.append({
        "txn_id": "TXN-OOD-003",
        "date": "2026-03-01",
        "amount": 12500.0,
        "counterparty": "Nexus Retail Pvt Ltd",
        "reference": "ORD-NEXUS-8003",
        "currency": "INR"
    })
    bank.append({
        "bank_txn_id": "BNK-OOD-8003",
        "date": "2026-03-05", # T+4 days later
        "amount": 12500.0,
        "narration": "CMS/NEFT/ORD-NEXUS-8003/Nexus Retail/UTR8003",
        "utr_reference": "UTR8003"
    })
    gateway.append({
        "payment_id": "pay_OOD_8003",
        "settled_amount": 12500.0,
        "fee": 0.0,
        "settlement_date": "2026-03-05",
        "order_ref": "ORD-NEXUS-8003"
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8003",
        "type": "BORDERLINE_DATE_DRIFT",
        "expected_status": "EXCEPTION", # Expect guardrail rejection due to T+4 lag
        "ledger_id": "TXN-OOD-003",
        "bank_id": "BNK-OOD-8003",
        "gateway_id": "pay_OOD_8003"
    })

    # 4. Adversarial Counterparty Collision (Homoglyph / Near Name on Same Day & Amount)
    # Ledger has "Apex Cloud Services", Bank narration says "Acme Cloud Systems" (ref similarity < 0.5)
    ledger.append({
        "txn_id": "TXN-OOD-004",
        "date": "2026-03-12",
        "amount": 50000.0,
        "counterparty": "Apex Cloud Services",
        "reference": "ORD-APEX-8004",
        "currency": "INR"
    })
    bank.append({
        "bank_txn_id": "BNK-OOD-8004",
        "date": "2026-03-12",
        "amount": 50000.0,
        "narration": "NEFT/ACME CLOUD SYSTEMS/UNKNOWN-UTR8004", # Colliding amount & date, different counterparty
        "utr_reference": "UTR8004"
    })
    gateway.append({
        "payment_id": "pay_OOD_8004",
        "settled_amount": 50000.0,
        "fee": 0.0,
        "settlement_date": "2026-03-12",
        "order_ref": "ORD-ACME-8004" # Conflicting order ref
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8004",
        "type": "CROSS_COUNTERPARTY_COLLISION",
        "expected_status": "EXCEPTION", # Must NOT force-match
        "ledger_id": "TXN-OOD-004",
        "bank_id": "BNK-OOD-8004",
        "gateway_id": "pay_OOD_8004"
    })

    # 5. Net Amount Collision vs Gross of Different Merchant
    # Merchant A Gross 30,000, Net 29,400 (fee: 600) vs Merchant B Gross 29,400 Net 29,400
    ledger.append({
        "txn_id": "TXN-OOD-005A",
        "date": "2026-03-14",
        "amount": 30000.0,
        "counterparty": "Zenith Enterprise ERP",
        "reference": "ORD-ZENITH-8005",
        "currency": "INR"
    })
    ledger.append({
        "txn_id": "TXN-OOD-005B",
        "date": "2026-03-14",
        "amount": 29400.0,
        "counterparty": "CloudScale Systems",
        "reference": "ORD-CLOUD-8005",
        "currency": "INR"
    })
    bank.append({
        "bank_txn_id": "BNK-OOD-8005B",
        "date": "2026-03-14",
        "amount": 29400.0,
        "narration": "NEFT/ORD-CLOUD-8005/CloudScale Systems/UTR8005B",
        "utr_reference": "UTR8005B"
    })
    gateway.append({
        "payment_id": "pay_OOD_8005B",
        "settled_amount": 29400.0,
        "fee": 0.0,
        "settlement_date": "2026-03-14",
        "order_ref": "ORD-CLOUD-8005"
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8005B",
        "type": "EXACT_MATCH",
        "expected_status": "MATCHED_EXACT",
        "ledger_id": "TXN-OOD-005B",
        "bank_id": "BNK-OOD-8005B",
        "gateway_id": "pay_OOD_8005B"
    })
    ground_truth.append({
        "group_id": "GRP-OOD-8005A",
        "type": "MISSING_IN_BANK",
        "expected_status": "EXCEPTION",
        "ledger_id": "TXN-OOD-005A",
        "bank_id": None,
        "gateway_id": None
    })

    return {
        "metadata": {
            "dataset_type": "OUT_OF_DISTRIBUTION_STRESS_TEST",
            "description": "Hand-crafted borderline stress test with 3.51% fees, T+4 date lags, and counterparty collisions.",
            "total_entities": len(ground_truth),
            "ledger_count": len(ledger),
            "bank_count": len(bank),
            "gateway_count": len(gateway)
        },
        "ledger": ledger,
        "bank": bank,
        "gateway": gateway,
        "ground_truth": ground_truth
    }

def run_stress_test_audit() -> Dict[str, Any]:
    """Runs reconciliation on the OOD stress batch and audits the results."""
    ood_data = generate_out_of_distribution_batch()
    recon_res = run_ai_reasoning_pipeline(ood_data, date_tolerance_days=3, fee_tolerance_pct=0.035)
    eval_res = evaluate_ground_truth_accuracy(ood_data, recon_res)
    
    return {
        "dataset_metadata": ood_data["metadata"],
        "summary": recon_res["summary"],
        "ground_truth_accuracy": eval_res,
        "matched_records": recon_res["matched_records"],
        "exceptions": recon_res["exceptions"]
    }

if __name__ == "__main__":
    import json
    result = run_stress_test_audit()
    print("=" * 75)
    print("  OUT-OF-DISTRIBUTION (OOD) ADVERSARIAL STRESS TEST AUDIT")
    print("=" * 75)
    gt = result["ground_truth_accuracy"]
    print(f"\n[Stress Test Ground-Truth Evaluation]")
    print(f"  * Precision: {gt['precision_pct']}% ({gt['true_positives']} TP, {gt['false_positives']} False Positives)")
    print(f"  * Recall:    {gt['recall_pct']}% ({gt['true_positives']}/{gt['total_true_matches_in_ground_truth']} matches found)")
    print(f"  * False Positives (Collisions): {gt['false_positives']}")
    print(f"  * Unresolved Exceptions Flagged: {len(result['exceptions'])}")
    print(f"\n[Stress Case Outcomes]")
    for exc in result["exceptions"]:
        print(f"  * [REJECTED & FLAGGED] {exc['id']}: {exc['plain_english_explanation']}")
        print(f"    Guardrail: {exc['guardrail_flag']}\n")

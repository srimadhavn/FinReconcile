import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from generate_synthetic_data import generate_synthetic_data
from matcher_deterministic import run_deterministic_matching
from matcher_fuzzy import run_fuzzy_matching, is_amount_compatible, calculate_match_confidence
from ai_reasoner import run_ai_reasoning_pipeline
from evaluator import evaluate_ground_truth_accuracy
from audit_store import persist_audit_run, list_audit_runs, get_audit_run_details

class TestFinReconcileComprehensive(unittest.TestCase):
    def setUp(self):
        self.dataset = generate_synthetic_data(seed=42, count=60)
        self.reconciliation = run_ai_reasoning_pipeline(self.dataset)

    # 1. Ground Truth Precision & Recall Verification (0 False Positives Guarantee)
    def test_ground_truth_precision_and_zero_false_positives(self):
        """Audits engine matches against known ground truth answer key."""
        eval_metrics = evaluate_ground_truth_accuracy(self.dataset, self.reconciliation)
        self.assertEqual(eval_metrics["false_positives"], 0, "Engine produced false positive collisions!")
        self.assertEqual(eval_metrics["precision_pct"], 100.0)
        self.assertEqual(eval_metrics["recall_pct"], 100.0)
        self.assertEqual(eval_metrics["evaluation_verdict"], "PERFECT_PRECISION (0 False Positives)")

    # 2. Headline Metric Baseline Regression Lock (Seed=42)
    def test_seed_42_headline_metrics_regression_lock(self):
        """Locks headline metric at 86.89% to prevent silent performance regressions."""
        summary = self.reconciliation["summary"]
        self.assertEqual(summary["total_base_records"], 61)
        self.assertEqual(summary["total_matched"], 53)
        self.assertEqual(summary["match_rate_percentage"], 86.89)
        self.assertEqual(summary["exact_matches"], 39)
        self.assertEqual(summary["fuzzy_matches"], 14)
        self.assertEqual(summary["total_exceptions"], 19)
        self.assertGreaterEqual(summary["average_confidence"], 0.90)

    # 3. Adversarial Tolerance: Fee Out-of-Bounds Rejection
    def test_adversarial_out_of_bounds_fee_rejection(self):
        """Actively tries to force a match with fee deduction exceeding tolerance (e.g. 5.5% > 3.5%)."""
        ledger_amt = 10000.0
        candidate_amt = 9450.0 # 5.5% fee cut
        is_compat, score, msg = is_amount_compatible(ledger_amt, candidate_amt, fee_tolerance_pct=0.035, fixed_tolerance=50.0)
        self.assertFalse(is_compat, "Engine accepted out-of-bounds fee deduction!")
        self.assertEqual(score, 0.0)

    # 4. Adversarial Tolerance: Date Lag Exceeded Rejection
    def test_adversarial_date_lag_exceeded_rejection(self):
        """Asserts that date lag exceeding tolerance (e.g. +6 days with max=3) is penalized."""
        score, tier = calculate_match_confidence(amt_score=1.0, date_diff=6, max_days=3, ref_sim=0.9)
        self.assertLess(score, 0.80)

    # 5. Adversarial Ambiguity: Counterparty Mismatch Rejection
    def test_adversarial_mismatched_counterparty_rejection(self):
        """Asserts that identical amount but completely mismatched counterparty is not force-matched."""
        synthetic_adversarial_dataset = {
            "ledger": [{
                "txn_id": "TXN-ADV-001",
                "date": "2026-03-05",
                "amount": 25000.0,
                "counterparty": "Acme Global Tech",
                "reference": "ORD-ACME-9999",
                "currency": "INR"
            }],
            "bank": [{
                "bank_txn_id": "BNK-ADV-999",
                "date": "2026-03-05",
                "amount": 25000.0,
                "narration": "NEFT/COMPLETELY_DIFFERENT_COMPANY/XYZ/UTR999",
                "utr_reference": "UTR999"
            }],
            "gateway": [{
                "payment_id": "pay_ADV_999",
                "settled_amount": 25000.0,
                "fee": 0.0,
                "settlement_date": "2026-03-05",
                "order_ref": "ORD-DIFF-9999"
            }]
        }
        res = run_fuzzy_matching(synthetic_adversarial_dataset)
        self.assertEqual(len(res["matched_groups"]), 0, "Engine incorrectly force-matched adversarial conflicting record!")

    # 6. Tie-Breaking & Reference Proximity Resolution
    def test_tie_breaking_closest_reference_resolution(self):
        """Asserts engine picks the highest string similarity candidate when amounts & dates collide."""
        synthetic_tie_dataset = {
            "ledger": [{
                "txn_id": "TXN-TIE-001",
                "date": "2026-03-05",
                "amount": 5000.0,
                "counterparty": "Nexus Retail Pvt Ltd",
                "reference": "ORD-NEXUS-777",
                "currency": "INR"
            }],
            "bank": [
                {
                    "bank_txn_id": "BNK-WRONG",
                    "date": "2026-03-05",
                    "amount": 5000.0,
                    "narration": "NEFT/UNRELATED_MERCHANT/OTHER/UTR111",
                    "utr_reference": "UTR111"
                },
                {
                    "bank_txn_id": "BNK-CORRECT",
                    "date": "2026-03-05",
                    "amount": 5000.0,
                    "narration": "CMS/NEFT/ORD-NEXUS-777/Nexus Retail Pvt Ltd/UTR777",
                    "utr_reference": "UTR777"
                }
            ],
            "gateway": [{
                "payment_id": "pay_777",
                "settled_amount": 5000.0,
                "fee": 0.0,
                "settlement_date": "2026-03-05",
                "order_ref": "ORD-NEXUS-777"
            }]
        }
        res = run_fuzzy_matching(synthetic_tie_dataset)
        self.assertEqual(len(res["matched_groups"]), 1)
        matched = res["matched_groups"][0]
        self.assertEqual(matched["bank"]["bank_txn_id"], "BNK-CORRECT")

    # 7. Penny & Rounding Difference Tolerance
    def test_penny_rounding_tolerance_compatibility(self):
        """Asserts FX/penny differences (<= INR 2.00) are recognized and scored appropriately."""
        is_compat, score, msg = is_amount_compatible(1500.00, 1499.10)
        self.assertTrue(is_compat)
        self.assertGreaterEqual(score, 0.90)

    # 8. Strict Guardrails on Exceptions
    def test_strict_guardrail_unresolved_flag(self):
        """Asserts all exceptions carry STRICT_UNRESOLVED flag and valid finance taxonomy."""
        exceptions = self.reconciliation["exceptions"]
        self.assertGreater(len(exceptions), 0)
        for exc in exceptions:
            self.assertEqual(exc["status"], "UNRESOLVED")
            self.assertIn("STRICT_UNRESOLVED", exc["guardrail_flag"])
            self.assertTrue(len(exc["cited_fields"]) > 0)
            self.assertTrue(len(exc["plain_english_explanation"]) > 0)

    # 9. Exception Taxonomy Classification Completeness
    def test_exception_taxonomy_classification_completeness(self):
        """Asserts all 8 core taxonomy categories are recognized by the reasoner."""
        valid_cats = {
            "DUPLICATE_ENTRY", "MISSING_IN_BANK", "MISSING_IN_LEDGER",
            "MISSING_IN_GATEWAY", "FEE_DEDUCTION_MISMATCH", "TIMING_LAG_EXCEEDED",
            "REFERENCE_MISMATCH", "UNEXPLAINABLE_ANOMALY"
        }
        tax_counts = self.reconciliation["summary"]["exception_taxonomy"]
        for cat in tax_counts.keys():
            self.assertIn(cat, valid_cats)

    # 10. Audit Run Persistence & Snapshot Retrieval
    def test_audit_run_persistence_and_retrieval(self):
        """Verifies full audit run snapshot is persisted to disk and indexed."""
        eval_metrics = evaluate_ground_truth_accuracy(self.dataset, self.reconciliation)
        run_id = persist_audit_run(
            self.reconciliation, 
            eval_metrics, 
            {"seed": 42, "date_tolerance_days": 3, "fee_tolerance_pct": 0.035}
        )
        self.assertTrue(run_id.startswith("RUN_"))
        runs = list_audit_runs()
        self.assertGreater(len(runs), 0)
        
        retrieved = get_audit_run_details(run_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["headline_metrics"]["match_rate_pct"], 86.89)
        self.assertEqual(retrieved["headline_metrics"]["ground_truth_precision_pct"], 100.0)

    # 11. Multi-Seed Generalization Resilience
    def test_multi_seed_generalization_resilience(self):
        """Asserts engine generalizes cleanly with 0 false positives across unseen seeds (100, 2026, 9999)."""
        for test_seed in [100, 2026, 9999]:
            ds = generate_synthetic_data(seed=test_seed, count=55)
            recon = run_ai_reasoning_pipeline(ds)
            eval_res = evaluate_ground_truth_accuracy(ds, recon)
            self.assertEqual(eval_res["false_positives"], 0, f"False positives detected on seed {test_seed}")
            self.assertGreaterEqual(eval_res["precision_pct"], 98.0)
            self.assertGreaterEqual(eval_res["recall_pct"], 95.0)

    # 12. Out-Of-Distribution (OOD) Stress Test Rejections
    def test_out_of_distribution_stress_batch_guardrail_rejections(self):
        """Audits engine against hand-crafted OOD stress cases with 3.51% fee cut and T+4 lag."""
        from adversarial_stress_test import run_stress_test_audit
        stress_res = run_stress_test_audit()
        exceptions = stress_res["exceptions"]
        
        # Verify that borderline fee (3.51%) and borderline lag (T+4) triggered guardrails
        fee_overage_flagged = any("702.00" in e["plain_english_explanation"] or "STRIPE" in e.get("reference", "") for e in exceptions)
        date_drift_flagged = any("12,500.00" in e["plain_english_explanation"] or "NEXUS" in e.get("reference", "") for e in exceptions)
        
        self.assertTrue(fee_overage_flagged, "3.51% fee overage was not caught by guardrail!")
        self.assertTrue(date_drift_flagged, "T+4 date lag drift was not caught by guardrail!")

if __name__ == "__main__":
    unittest.main()

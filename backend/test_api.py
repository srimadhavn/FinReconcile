import os
import sys
import unittest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(__file__))
from main import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.client.post("/api/regenerate", json={"seed": 42, "count": 60})

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_dataset(self):
        res = self.client.get("/api/dataset")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ledger", data)
        self.assertIn("bank", data)
        self.assertIn("gateway", data)

    def test_reconcile_endpoint_with_ground_truth(self):
        res = self.client.post("/api/reconcile", json={
            "seed": 42,
            "count": 60,
            "date_tolerance_days": 3,
            "fee_tolerance_pct": 0.035
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("run_id", data)
        self.assertIn("phase1", data)
        self.assertIn("phase2", data)
        self.assertIn("reconciliation", data)
        self.assertIn("ground_truth_accuracy", data)
        
        gt = data["ground_truth_accuracy"]
        self.assertEqual(gt["precision_pct"], 100.0)
        self.assertEqual(gt["false_positives"], 0)

    def test_audit_history_endpoints(self):
        # First trigger a reconciliation to create run
        reconcile_res = self.client.post("/api/reconcile", json={"seed": 42, "count": 60})
        run_id = reconcile_res.json()["run_id"]
        
        # List runs
        runs_res = self.client.get("/api/audit/runs")
        self.assertEqual(runs_res.status_code, 200)
        runs = runs_res.json()
        self.assertGreater(len(runs), 0)
        
        # Get specific run details
        detail_res = self.client.get(f"/api/audit/runs/{run_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["run_id"], run_id)
        self.assertIn("headline_metrics", detail)

    def test_export_csv(self):
        res = self.client.get("/api/export/csv?date_tolerance_days=3&fee_tolerance_pct=0.035")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/csv", res.headers["content-type"])
        self.assertTrue(len(res.text) > 100)

    def test_natural_language_query(self):
        # 1. Data query with amount filter
        res1 = self.client.post("/api/query", json={"query": "Show exceptions above 10000"})
        self.assertEqual(res1.status_code, 200)
        d1 = res1.json()
        self.assertEqual(d1["intent"], "DATA_QUERY")
        self.assertGreater(len(d1["filtered_exceptions"]), 0)
        self.assertIn("answer", d1)

        # 2. Meta query (should not dump exceptions)
        res2 = self.client.post("/api/query", json={"query": "what do you do?"})
        self.assertEqual(res2.status_code, 200)
        d2 = res2.json()
        self.assertEqual(d2["intent"], "META")
        self.assertEqual(len(d2["filtered_exceptions"]), 0)
        self.assertTrue("reconciliation" in d2["answer"].lower() or "financial" in d2["answer"].lower())

        # 3. Greeting (should not dump exceptions)
        res3 = self.client.post("/api/query", json={"query": "hello"})
        self.assertEqual(res3.status_code, 200)
        d3 = res3.json()
        self.assertEqual(d3["intent"], "GREETING")
        self.assertEqual(len(d3["filtered_exceptions"]), 0)

        # 4. Nonsense query (should fail gracefully)
        res4 = self.client.post("/api/query", json={"query": "asdkjfh293"})
        self.assertEqual(res4.status_code, 200)
        d4 = res4.json()
        self.assertEqual(d4["intent"], "NONSENSE")
        self.assertEqual(len(d4["filtered_exceptions"]), 0)
        self.assertTrue("could not" in d4["answer"].lower() or "no" in d4["answer"].lower())

    def test_csv_templates_endpoints(self):
        # 1. Get all templates JSON
        res = self.client.get("/api/csv/templates")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("ledger", data)
        self.assertIn("bank", data)
        self.assertIn("gateway", data)

        # 2. Download specific template CSV
        res_ldg = self.client.get("/api/csv/template/ledger")
        self.assertEqual(res_ldg.status_code, 200)
        self.assertIn("txn_id", res_ldg.text)

    def test_custom_csv_upload(self):
        ledger_csv = "txn_id,date,amount,counterparty,reference\nTXN-01,2026-03-01,1000.00,Acme Corp,REF-01\nTXN-02,2026-03-02,2000.00,Beta Inc,REF-02\n"
        bank_csv = "bank_txn_id,date,amount,narration,utr_reference\nBNK-01,2026-03-01,1000.00,NEFT ACME CORP REF-01,UTR-01\nBNK-02,2026-03-03,2000.00,RTGS BETA INC REF-02,UTR-02\n"
        gateway_csv = "payment_id,settlement_date,gross_amount,fee_deducted,settled_amount\nPAY-01,2026-03-01,1000.00,0.00,1000.00\nPAY-02,2026-03-02,2000.00,0.00,2000.00\n"

        files = {
            "ledger_file": ("test_ledger.csv", ledger_csv.encode("utf-8"), "text/csv"),
            "bank_file": ("test_bank.csv", bank_csv.encode("utf-8"), "text/csv"),
            "gateway_file": ("test_gateway.csv", gateway_csv.encode("utf-8"), "text/csv")
        }
        data = {
            "date_tolerance_days": "3",
            "fee_tolerance_pct": "0.035"
        }

        res = self.client.post("/api/upload/csv", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        d = res.json()
        self.assertEqual(d["status"], "success")
        self.assertTrue(d["is_custom_upload"])
        self.assertIn("run_id", d)
        self.assertIn("reconciliation", d)
        self.assertEqual(d["reconciliation"]["summary"]["total_matched"], 2)

if __name__ == "__main__":
    unittest.main()



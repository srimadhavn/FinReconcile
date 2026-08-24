import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

def generate_synthetic_data(seed: int = 42, count: int = 60) -> Dict[str, Any]:
    random.seed(seed)
    
    start_date = datetime(2026, 3, 1)
    
    counterparties = [
        ("Acme Global Tech", "ACME", "corp"),
        ("Stripe Billing Solutions", "STRIPE", "saas"),
        ("CloudScale Systems", "CLOUD", "vendor"),
        ("Apex Cloud Services", "APEX", "infra"),
        ("Nexus Retail Pvt Ltd", "NEXUS", "merchant"),
        ("FinVantage Capital", "FINVAN", "financial"),
        ("BlueHorizon Logistics", "BLUEHOR", "logistics"),
        ("Quantum Data Labs", "QUANTUM", "software"),
        ("Vertex Digital Media", "VERTEX", "marketing"),
        ("Zenith Enterprise ERP", "ZENITH", "subscription")
    ]
    
    ledger_records: List[Dict[str, Any]] = []
    bank_records: List[Dict[str, Any]] = []
    gateway_records: List[Dict[str, Any]] = []
    ground_truth: List[Dict[str, Any]] = []
    
    # Calculate distributions
    # Total count = 60
    # Exact: 37 (~62%)
    # Timing: 6 (~10%)
    # Amount/Fee: 5 (~8%)
    # Narration Fuzz: 5 (~8%)
    # Missing: 3 (~5%)
    # Duplicate: 2 (~3.5%)
    # True Exception: 2 (~3.5%)
    
    exact_count = int(count * 0.62)
    timing_count = int(count * 0.10)
    fee_count = int(count * 0.08)
    fuzz_count = int(count * 0.08)
    missing_count = int(count * 0.05)
    dup_count = int(count * 0.035)
    anomaly_count = count - (exact_count + timing_count + fee_count + fuzz_count + missing_count + dup_count)
    
    txn_index = 1000
    
    def next_id():
        nonlocal txn_index
        txn_index += 1
        return txn_index

    # 1. EXACT MATCHES
    for i in range(exact_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        amount = round(random.uniform(500.0, 75000.0), 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        utr = f"UTR2026{idx:06d}X"
        pay_id = f"pay_{idx:08d}"
        
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": txn_date,
            "amount": amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": txn_date,
            "amount": amount,
            "narration": f"CMS/NEFT/{ref_code}/{cp_name}/UTIB0001/{utr}",
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": amount,
            "fee": 0.0,
            "settlement_date": txn_date,
            "order_ref": ref_code
        })
        
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "EXACT_MATCH",
            "expected_status": "MATCHED_EXACT",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": amount,
            "notes": "Exact 3-way match across amount, date, and reference."
        })

    # 2. TIMING MISMATCHES (T+1 to T+3 Settlement Lag)
    for i in range(timing_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 18)
        ldg_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        bank_lag = random.choice([1, 2])
        gateway_lag = random.choice([1, 2, 3])
        bank_date = (start_date + timedelta(days=day_offset + bank_lag)).strftime("%Y-%m-%d")
        gw_date = (start_date + timedelta(days=day_offset + gateway_lag)).strftime("%Y-%m-%d")
        amount = round(random.uniform(1200.0, 45000.0), 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        utr = f"UTR2026{idx:06d}T"
        pay_id = f"pay_{idx:08d}"
        
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": ldg_date,
            "amount": amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": bank_date,
            "amount": amount,
            "narration": f"SETTLEMENT/{ref_code}/{cp_name}/{utr}",
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": amount,
            "fee": 0.0,
            "settlement_date": gw_date,
            "order_ref": ref_code
        })
        
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "TIMING_MISMATCH",
            "expected_status": "MATCHED_FUZZY",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": amount,
            "notes": f"T+{bank_lag} bank settlement lag, T+{gateway_lag} gateway settlement lag."
        })

    # 3. AMOUNT MISMATCHES (Gateway Fee Deductions / Net Settlements)
    for i in range(fee_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        gross_amount = round(random.uniform(5000.0, 80000.0), 2)
        fee_pct = random.choice([0.015, 0.02, 0.0236]) # 1.5% to 2% + GST
        fee = round(gross_amount * fee_pct, 2)
        net_amount = round(gross_amount - fee, 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        utr = f"UTR2026{idx:06d}F"
        pay_id = f"pay_{idx:08d}"
        
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": txn_date,
            "amount": gross_amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        # Bank receives net settled amount
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": txn_date,
            "amount": net_amount,
            "narration": f"RAZORPAY/NET-SETTLE/{ref_code}/{utr}",
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": net_amount,
            "fee": fee,
            "settlement_date": txn_date,
            "order_ref": ref_code
        })
        
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "AMOUNT_FEE_MISMATCH",
            "expected_status": "MATCHED_FUZZY",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": gross_amount,
            "notes": f"Gateway fee of INR {fee} deducted from Gross INR {gross_amount}."
        })

    # 4. REFERENCE / NARRATION FUZZ (Garbled text, truncated refs, missing prefix)
    for i in range(fuzz_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        amount = round(random.uniform(2000.0, 35000.0), 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        garbled_narrations = [
            f"UPI/{idx}/P2M/{cp_name[:6].upper()}/YESB0001",
            f"POS DEBIT TRF {idx} {cp_code}",
            f"IMPS/P2A/{idx}/{cp_name.replace(' ', '')[:8]}",
            f"NEFT CR-{idx}-{cp_code}-CORP"
        ]
        narration = random.choice(garbled_narrations)
        utr = f"UTR2026{idx:06d}Z"
        pay_id = f"pay_{idx:08d}"
        
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": txn_date,
            "amount": amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": txn_date,
            "amount": amount,
            "narration": narration,
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": amount,
            "fee": 0.0,
            "settlement_date": txn_date,
            "order_ref": f"{cp_code}-{idx}" # partial order ref
        })
        
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "REFERENCE_NARRATION_FUZZ",
            "expected_status": "MATCHED_FUZZY",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": amount,
            "notes": "Bank narration garbled and order_ref prefix omitted."
        })

    # 5. MISSING RECORDS (In Ledger but not Bank, or in Bank but not Ledger)
    for i in range(missing_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        amount = round(random.uniform(4000.0, 25000.0), 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        
        if i % 2 == 0:
            # Case A: In ledger & gateway, but dropped from Bank (payment failed settlement)
            ledger_records.append({
                "txn_id": f"TXN-LDG-{idx}",
                "date": txn_date,
                "amount": amount,
                "counterparty": cp_name,
                "reference": ref_code,
                "currency": "INR"
            })
            gateway_records.append({
                "payment_id": f"pay_{idx:08d}",
                "settled_amount": amount,
                "fee": 0.0,
                "settlement_date": txn_date,
                "order_ref": ref_code
            })
            ground_truth.append({
                "group_id": f"GRP-{idx}",
                "type": "MISSING_IN_BANK",
                "expected_status": "EXCEPTION",
                "ledger_id": f"TXN-LDG-{idx}",
                "bank_id": None,
                "gateway_id": f"pay_{idx:08d}",
                "base_amount": amount,
                "notes": "Failed settlement: present in Ledger and Gateway, but missing from Bank Statement."
            })
        else:
            # Case B: In Bank only (unrecorded direct wire transfer)
            bank_records.append({
                "bank_txn_id": f"BNK-{idx}",
                "date": txn_date,
                "amount": amount,
                "narration": f"DIRECT WIRE/UNIDENTIFIED CREDIT/{cp_name}",
                "utr_reference": f"UTR2026{idx:06d}M"
            })
            ground_truth.append({
                "group_id": f"GRP-{idx}",
                "type": "MISSING_IN_LEDGER",
                "expected_status": "EXCEPTION",
                "ledger_id": None,
                "bank_id": f"BNK-{idx}",
                "gateway_id": None,
                "base_amount": amount,
                "notes": "Unrecorded credit: present in Bank Statement, missing in Ledger & Gateway."
            })

    # 6. DUPLICATE RECORDS (Double posting in ledger or bank webhook)
    for i in range(dup_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        amount = round(random.uniform(8000.0, 18000.0), 2)
        ref_code = f"ORD-{cp_code}-{idx}"
        utr = f"UTR2026{idx:06d}D"
        pay_id = f"pay_{idx:08d}"
        
        # Primary ledger record
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": txn_date,
            "amount": amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        # Duplicate ledger entry (ERP glitch)
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}-DUP",
            "date": txn_date,
            "amount": amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": txn_date,
            "amount": amount,
            "narration": f"NEFT/{ref_code}/{cp_name}/{utr}",
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": amount,
            "fee": 0.0,
            "settlement_date": txn_date,
            "order_ref": ref_code
        })
        
        # Ground truth for primary match
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "EXACT_MATCH",
            "expected_status": "MATCHED_EXACT",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": amount,
            "notes": "Primary valid match before duplicate voucher."
        })
        
        # Ground truth for duplicate exception
        ground_truth.append({
            "group_id": f"GRP-{idx}-DUP",
            "type": "DUPLICATE_ENTRY",
            "expected_status": "EXCEPTION",
            "ledger_id": f"TXN-LDG-{idx}-DUP",
            "bank_id": None,
            "gateway_id": None,
            "base_amount": amount,
            "notes": "Duplicate ledger entry created with identical amount and reference."
        })

    # 7. TRUE EXCEPTIONS (Genuinely unexplainable anomalies / chargeback / wrong account)
    for i in range(anomaly_count):
        idx = next_id()
        cp_name, cp_code, _ = random.choice(counterparties)
        day_offset = random.randint(0, 20)
        txn_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        ldg_amount = round(random.uniform(30000.0, 90000.0), 2)
        bank_amount = round(ldg_amount * 0.42, 2) # severely mismatched amount
        ref_code = f"ORD-{cp_code}-{idx}"
        utr = f"UTR2026{idx:06d}X"
        pay_id = f"pay_{idx:08d}"
        
        ledger_records.append({
            "txn_id": f"TXN-LDG-{idx}",
            "date": txn_date,
            "amount": ldg_amount,
            "counterparty": cp_name,
            "reference": ref_code,
            "currency": "INR"
        })
        
        bank_records.append({
            "bank_txn_id": f"BNK-{idx}",
            "date": txn_date,
            "amount": bank_amount,
            "narration": f"DISPUTED TRF/{ref_code}/CHARGEBACK-HOLD",
            "utr_reference": utr
        })
        
        gateway_records.append({
            "payment_id": pay_id,
            "settled_amount": ldg_amount,
            "fee": 0.0,
            "settlement_date": txn_date,
            "order_ref": ref_code
        })
        
        ground_truth.append({
            "group_id": f"GRP-{idx}",
            "type": "UNEXPLAINABLE_ANOMALY",
            "expected_status": "EXCEPTION",
            "ledger_id": f"TXN-LDG-{idx}",
            "bank_id": f"BNK-{idx}",
            "gateway_id": pay_id,
            "base_amount": ldg_amount,
            "notes": f"Severe amount mismatch (Ledger: INR {ldg_amount} vs Bank: INR {bank_amount}) with chargeback hold flag."
        })

    # Shuffle to ensure realistic ordering across files
    random.shuffle(ledger_records)
    random.shuffle(bank_records)
    random.shuffle(gateway_records)
    
    return {
        "metadata": {
            "seed": seed,
            "generated_at": datetime.now().isoformat(),
            "ledger_count": len(ledger_records),
            "bank_count": len(bank_records),
            "gateway_count": len(gateway_records),
            "total_records": len(ledger_records) + len(bank_records) + len(gateway_records)
        },
        "ledger": ledger_records,
        "bank": bank_records,
        "gateway": gateway_records,
        "ground_truth": ground_truth
    }

if __name__ == "__main__":
    import os
    data = generate_synthetic_data(seed=42, count=60)
    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "synthetic_dataset.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Generated synthetic dataset with seed=42:")
    print(f" - Ledger records:  {data['metadata']['ledger_count']}")
    print(f" - Bank records:    {data['metadata']['bank_count']}")
    print(f" - Gateway records: {data['metadata']['gateway_count']}")
    print(f"Saved to {out_path}")

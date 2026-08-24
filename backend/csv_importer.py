import csv
import io
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

def normalize_header(h: str) -> str:
    """Normalizes column headers (lowercase, stripped, alphanumeric with underscores)."""
    return re.sub(r'[^a-z0-9_]', '', h.lower().strip().replace(' ', '_').replace('-', '_'))

def parse_amount(val: Any) -> float:
    """Parses clean numeric amount from currency strings (e.g. ₹12,345.50, INR 500, (100))."""
    if val is None:
        return 0.0
    s = str(val).strip()
    if not s:
        return 0.0
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1].strip()
    elif s.startswith("-"):
        is_negative = True
        s = s[1:].strip()
        
    # Clean currency symbols, commas, quotes
    s = re.sub(r'[₹$€£, ]', '', s)
    s = re.sub(r'(?i)\b(inr|rs\.?|usd)\b', '', s).strip()
    try:
        amt = float(s)
        return -amt if is_negative else amt
    except ValueError:
        return 0.0

def parse_date(val: Any) -> str:
    """Parses and normalizes date string to YYYY-MM-DD format."""
    if not val:
        return datetime.now().strftime("%Y-%m-%d")
    s = str(val).strip()
    formats = [
        "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s

def parse_ledger_csv(content: str) -> List[Dict[str, Any]]:
    """Parses General Ledger CSV content into normalized records."""
    f = io.StringIO(content.strip())
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return []
    
    headers = [normalize_header(h) for h in raw_headers]
    records = []
    
    for idx, row in enumerate(reader, start=1):
        if not row or not any(field.strip() for field in row):
            continue
        d = dict(zip(headers, row))
        
        txn_id = d.get('txnid') or d.get('id') or d.get('txn_id') or d.get('voucher_no') or d.get('voucherno') or f"LDG-{idx:04d}"
        date_val = d.get('date') or d.get('txndate') or d.get('txn_date') or d.get('posting_date') or ""
        amt_val = d.get('amount') or d.get('amt') or d.get('debit') or d.get('credit') or 0.0
        cp_val = d.get('counterparty') or d.get('vendor') or d.get('customer') or d.get('party') or d.get('account') or "Unspecified Entity"
        ref_val = d.get('reference') or d.get('ref') or d.get('invoiceno') or d.get('invoice_no') or d.get('order_id') or txn_id
        
        records.append({
            "txn_id": str(txn_id).strip(),
            "date": parse_date(date_val),
            "amount": parse_amount(amt_val),
            "counterparty": str(cp_val).strip(),
            "reference": str(ref_val).strip(),
            "source": "Ledger"
        })
    return records

def parse_bank_csv(content: str) -> List[Dict[str, Any]]:
    """Parses Bank Statement CSV content into normalized records."""
    f = io.StringIO(content.strip())
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return []
    
    headers = [normalize_header(h) for h in raw_headers]
    records = []
    
    for idx, row in enumerate(reader, start=1):
        if not row or not any(field.strip() for field in row):
            continue
        d = dict(zip(headers, row))
        
        bank_id = d.get('banktxnid') or d.get('bank_txn_id') or d.get('id') or d.get('txnid') or d.get('cheque_no') or f"BNK-{idx:04d}"
        date_val = d.get('date') or d.get('valuedate') or d.get('value_date') or d.get('txn_date') or ""
        amt_val = d.get('amount') or d.get('amt') or d.get('credit') or d.get('deposit') or 0.0
        narr_val = d.get('narration') or d.get('description') or d.get('remarks') or d.get('particulars') or "Direct Bank Transfer"
        utr_val = d.get('utrreference') or d.get('utr_reference') or d.get('utr') or d.get('ref') or d.get('reference') or bank_id
        
        records.append({
            "bank_txn_id": str(bank_id).strip(),
            "date": parse_date(date_val),
            "amount": parse_amount(amt_val),
            "narration": str(narr_val).strip(),
            "utr_reference": str(utr_val).strip(),
            "source": "Bank Statement"
        })
    return records

def parse_gateway_csv(content: str) -> List[Dict[str, Any]]:
    """Parses Payment Gateway Settlement CSV content into normalized records."""
    f = io.StringIO(content.strip())
    reader = csv.reader(f)
    try:
        raw_headers = next(reader)
    except StopIteration:
        return []
    
    headers = [normalize_header(h) for h in raw_headers]
    records = []
    
    for idx, row in enumerate(reader, start=1):
        if not row or not any(field.strip() for field in row):
            continue
        d = dict(zip(headers, row))
        
        payment_id = d.get('paymentid') or d.get('payment_id') or d.get('id') or d.get('txnid') or d.get('order_id') or f"GTW-{idx:04d}"
        settle_date = d.get('settlementdate') or d.get('settlement_date') or d.get('date') or d.get('settled_at') or ""
        gross_val = d.get('grossamount') or d.get('gross_amount') or d.get('amount') or 0.0
        fee_val = d.get('feededucted') or d.get('fee_deducted') or d.get('fee') or d.get('mdr') or d.get('tax') or 0.0
        settled_val = d.get('settledamount') or d.get('settled_amount') or d.get('netamount') or d.get('net_amount') or ""
        
        gross = parse_amount(gross_val)
        fee = parse_amount(fee_val)
        settled = parse_amount(settled_val) if settled_val else (gross - fee)
        
        ref_val = d.get('order_ref') or d.get('orderref') or d.get('reference') or d.get('ref') or str(payment_id).strip()

        records.append({
            "payment_id": str(payment_id).strip(),
            "order_ref": str(ref_val).strip(),
            "settlement_date": parse_date(settle_date),
            "gross_amount": gross,
            "fee_deducted": fee,
            "settled_amount": settled,
            "amount": gross,
            "source": "Gateway Settlement"
        })
    return records

def generate_sample_csv_templates() -> Dict[str, str]:
    """Generates clean sample CSV templates for user reference."""
    ledger_template = """txn_id,date,amount,counterparty,reference
TXN-1001,2026-03-05,25000.00,Acme Global Tech,ORD-ACME-1001
TXN-1002,2026-03-06,14386.50,Nexus Retail Pvt Ltd,ORD-NEXUS-1002
TXN-1003,2026-03-08,8071.91,Zenith Enterprise ERP,ORD-ZENITH-1003
TXN-1004,2026-03-09,58360.26,Apex Cloud Services,ORD-APEX-1004
TXN-1005,2026-03-10,37938.71,Vertex Digital Media,ORD-VERTEX-1005
"""

    bank_template = """bank_txn_id,date,amount,narration,utr_reference
BNK-1001,2026-03-05,25000.00,CMS/ACME GLOBAL/INV-1001/SETTL,UTR-BNK-1001
BNK-1002,2026-03-07,14386.50,NEFT-NEXUS RETAIL-ORD-NEXUS-1002,UTR-BNK-1002
BNK-1003,2026-03-08,8071.91,RTGS-ZENITH ERP-ORD-ZENITH-1003,UTR-BNK-1003
BNK-1004,2026-03-11,58360.26,DISPUTED TRF/ORD-APEX-1004/HOLD,UTR-BNK-1004
BNK-1005,2026-03-12,37000.00,ACH CR VERTEX MEDIA ORD-VERTEX-1005,UTR-BNK-1005
"""

    gateway_template = """payment_id,settlement_date,gross_amount,fee_deducted,settled_amount
PAY-1001,2026-03-05,25000.00,0.00,25000.00
PAY-1002,2026-03-06,14386.50,302.12,14084.38
PAY-1003,2026-03-08,8071.91,169.51,7902.40
PAY-1004,2026-03-09,58360.26,1225.56,57134.70
PAY-1005,2026-03-10,37938.71,796.71,37142.00
"""

    return {
        "ledger": ledger_template,
        "bank": bank_template,
        "gateway": gateway_template
    }

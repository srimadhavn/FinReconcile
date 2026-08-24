import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

AUDIT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "audit_runs")
HISTORY_INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "audit_history.json")

def init_audit_store():
    os.makedirs(AUDIT_DIR, exist_ok=True)
    if not os.path.exists(HISTORY_INDEX_PATH):
        with open(HISTORY_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

def persist_audit_run(
    reconciliation_data: Dict[str, Any],
    ground_truth_eval: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """
    Persists a complete immutable snapshot of a reconciliation execution run
    to disk with timestamp, seed, metrics, and full audit logs.
    """
    init_audit_store()
    
    timestamp_iso = datetime.now().isoformat()
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    seed = parameters.get("seed", 42)
    run_id = f"RUN_{run_timestamp}_S{seed}"
    
    summary = reconciliation_data.get("summary") or reconciliation_data.get("reconciliation", {}).get("summary", {})
    
    run_record = {
        "run_id": run_id,
        "timestamp": timestamp_iso,
        "parameters": parameters,
        "headline_metrics": {
            "match_rate_pct": summary.get("match_rate_percentage", 0),
            "matched_records": summary.get("total_matched", 0),
            "total_base_records": summary.get("total_base_records", 0),
            "total_exceptions": summary.get("total_exceptions", 0),
            "exact_matches": summary.get("exact_matches", 0),
            "fuzzy_matches": summary.get("fuzzy_matches", 0),
            "average_confidence_pct": round(summary.get("average_confidence", 0) * 100, 1),
            "ground_truth_precision_pct": ground_truth_eval.get("precision_pct", 100.0),
            "ground_truth_recall_pct": ground_truth_eval.get("recall_pct", 100.0),
            "false_positives": ground_truth_eval.get("false_positives", 0),
            "verdict": ground_truth_eval.get("evaluation_verdict", "PERFECT_PRECISION")
        },
        "ground_truth_evaluation": ground_truth_eval,
        "full_reconciliation": reconciliation_data
    }
    
    # Save full snapshot file
    file_path = os.path.join(AUDIT_DIR, f"{run_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)
        
    # Update index
    try:
        with open(HISTORY_INDEX_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []
        
    # Prepend new run index entry
    index_entry = {
        "run_id": run_id,
        "timestamp": timestamp_iso,
        "seed": seed,
        "match_rate_pct": summary.get("match_rate_percentage", 0),
        "total_matched": summary.get("total_matched", 0),
        "total_base": summary.get("total_base_records", 0),
        "precision_pct": ground_truth_eval.get("precision_pct", 100.0),
        "recall_pct": ground_truth_eval.get("recall_pct", 100.0),
        "exceptions_count": summary.get("total_exceptions", 0),
        "file_path": file_path
    }
    
    # Keep last 50 runs
    history = [index_entry] + [h for h in history if h.get("run_id") != run_id][:49]
    with open(HISTORY_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
        
    return run_id

def list_audit_runs() -> List[Dict[str, Any]]:
    init_audit_store()
    try:
        with open(HISTORY_INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def get_audit_run_details(run_id: str) -> Optional[Dict[str, Any]]:
    init_audit_store()
    file_path = os.path.join(AUDIR_DIR := AUDIT_DIR, f"{run_id}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

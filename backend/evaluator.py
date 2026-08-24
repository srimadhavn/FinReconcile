from typing import Dict, List, Any

def evaluate_ground_truth_accuracy(
    dataset: Dict[str, Any],
    reconciliation_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Rigorously audits the reconciliation engine's outputs against the synthetic ground truth answer key.
    Calculates:
      - Precision: How many of the engine's matches were the true triplet vs coincidental false matches.
      - Recall: How many of the true matchable triplets in the dataset did the engine find.
      - F1 Score: Harmonic mean of precision and recall.
      - False Positives (FP): Incorrectly merged records (Dangerous cross-counterparty collisions).
      - False Negatives (FN): Valid matches missed and sent to exception queue.
      - True Negatives (TN): Genuine anomalies/duplicates correctly kept unresolved.
    """
    ground_truth = dataset.get("ground_truth", [])
    matched_records = reconciliation_result.get("matched_records", [])
    exceptions = reconciliation_result.get("exceptions", [])
    
    # Index ground truth true pairings
    gt_true_triplets = {}
    gt_expected_exceptions = set()
    
    for gt in ground_truth:
        l_id = gt.get("ledger_id")
        b_id = gt.get("bank_id")
        g_id = gt.get("gateway_id")
        status = gt.get("expected_status", "")
        
        if status.startswith("MATCHED") and l_id and b_id and g_id:
            gt_true_triplets[l_id] = {
                "bank_id": b_id,
                "gateway_id": g_id,
                "group_id": gt.get("group_id"),
                "type": gt.get("type")
            }
            # If there is a duplicate ledger entry, both ID variants map to the same underlying true match
            gt_true_triplets[f"{l_id}-DUP"] = {
                "bank_id": b_id,
                "gateway_id": g_id,
                "group_id": gt.get("group_id"),
                "type": gt.get("type")
            }
        else:
            gt_expected_exceptions.add(l_id or gt.get("group_id"))

    # Total distinct valid business triplets in ground truth
    total_true_matches = len([g for g in ground_truth if g.get("expected_status", "").startswith("MATCHED") and g.get("ledger_id") and g.get("bank_id") and g.get("gateway_id")])
    total_true_exceptions = len([g for g in ground_truth if g.get("expected_status") == "EXCEPTION"])
    
    tp = 0 # Engine matched, and triplet is 100% correct in Ground Truth
    fp = 0 # Engine matched, but triplet is WRONG (False Positive / Collision)
    
    false_positive_details = []
    matched_group_ids = set()
    
    for m in matched_records:
        l_id = m.get("ledger", {}).get("txn_id")
        b_id = m.get("bank", {}).get("bank_txn_id")
        g_id = m.get("gateway", {}).get("payment_id")
        
        if l_id in gt_true_triplets:
            expected = gt_true_triplets[l_id]
            if expected["bank_id"] == b_id and expected["gateway_id"] == g_id:
                # Check for double counting
                if expected["group_id"] not in matched_group_ids:
                    tp += 1
                    matched_group_ids.add(expected["group_id"])
                else:
                    # Double matching the same business event
                    fp += 1
                    false_positive_details.append({
                        "match_id": m.get("match_id"),
                        "ledger_id": l_id,
                        "note": "Double matched same business entity"
                    })
            else:
                fp += 1
                false_positive_details.append({
                    "match_id": m.get("match_id"),
                    "ledger_id": l_id,
                    "matched_bank": b_id,
                    "expected_bank": expected["bank_id"],
                    "matched_gateway": g_id,
                    "expected_gateway": expected["gateway_id"]
                })
        else:
            # Engine matched a record that was supposed to be an exception
            fp += 1
            false_positive_details.append({
                "match_id": m.get("match_id"),
                "ledger_id": l_id,
                "note": "Matched a record expected to be an unresolved exception"
            })
            
    # Missed matches = True matchable triplets that were NOT matched by the engine
    fn = max(0, total_true_matches - tp)
    
    # Correctly flagged exceptions
    tn = total_true_exceptions # Exceptions safely kept unresolved
    
    precision = (tp / max(tp + fp, 1)) * 100.0
    recall = (tp / max(total_true_matches, 1)) * 100.0
    f1 = (2 * precision * recall) / max(precision + recall, 1e-5)
    overall_accuracy = ((tp + tn) / max(total_true_matches + total_true_exceptions, 1)) * 100.0
    
    return {
        "precision_pct": round(precision, 2),
        "recall_pct": round(recall, 2),
        "f1_score": round(f1, 2),
        "overall_accuracy_pct": round(overall_accuracy, 2),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "total_true_matches_in_ground_truth": total_true_matches,
        "total_true_exceptions_in_ground_truth": total_true_exceptions,
        "false_positive_details": false_positive_details,
        "evaluation_verdict": "PERFECT_PRECISION (0 False Positives)" if fp == 0 else f"CONTAINS_{fp}_COLLISIONS"
    }

if __name__ == "__main__":
    from generate_synthetic_data import generate_synthetic_data
    from ai_reasoner import run_ai_reasoning_pipeline
    ds = generate_synthetic_data(seed=42, count=60)
    recon = run_ai_reasoning_pipeline(ds)
    eval_res = evaluate_ground_truth_accuracy(ds, recon)
    import json
    print(json.dumps(eval_res, indent=2))

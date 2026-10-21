"""Evaluation metrics for verification, retrieval, uncertainty calibration, and abstention."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def compute_verification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute Accuracy, Macro-F1, Precision, and Recall across 3 classes."""
    if not y_true or not y_pred:
        return {"accuracy": 0.0, "macro_f1": 0.0, "macro_precision": 0.0, "macro_recall": 0.0}

    canonical_labels = labels or ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=canonical_labels, average="macro", zero_division=0
    )

    per_class_p, per_class_r, per_class_f1, per_class_support = precision_recall_fscore_support(
        y_true, y_pred, labels=canonical_labels, average=None, zero_division=0
    )

    per_class = {}
    for lbl, p, r, f, s in zip(canonical_labels, per_class_p, per_class_r, per_class_f1, per_class_support):
        per_class[lbl] = {
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f), 4),
            "support": int(s),
        }

    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(float(f1_macro), 4),
        "macro_precision": round(float(p_macro), 4),
        "macro_recall": round(float(r_macro), 4),
        "per_class": per_class,
        "total_evaluated": len(y_true),
    }


def compute_retrieval_metrics(
    gold_ids_list: List[List[str]],
    retrieved_ids_list: List[List[str]],
    k: int = 5,
) -> Dict[str, float]:
    """Compute Recall@k, Precision@k, and MRR for evidence retrieval."""
    if not gold_ids_list:
        return {"recall@k": 0.0, "precision@k": 0.0, "mrr": 0.0}

    recalls = []
    precisions = []
    reciprocal_ranks = []

    for gold, retrieved in zip(gold_ids_list, retrieved_ids_list):
        if not gold:
            continue
        gold_set = set(gold)
        top_k = retrieved[:k]

        hits = sum(1 for doc_id in top_k if doc_id in gold_set)
        recalls.append(hits / len(gold_set))
        precisions.append(hits / max(1, len(top_k)))

        rr = 0.0
        for rank, doc_id in enumerate(top_k, 1):
            if doc_id in gold_set:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    return {
        f"recall@{k}": round(float(np.mean(recalls)), 4) if recalls else 0.0,
        f"precision@{k}": round(float(np.mean(precisions)), 4) if precisions else 0.0,
        "mrr": round(float(np.mean(reciprocal_ranks)), 4) if reciprocal_ranks else 0.0,
    }


def compute_calibration_metrics(
    confidences: List[float],
    accuracies: List[int],  # 1 if prediction matches true, 0 otherwise
    num_bins: int = 5,
) -> Dict[str, float]:
    """Compute Expected Calibration Error (ECE) and Brier Score."""
    if not confidences or not accuracies:
        return {"ece": 0.0, "brier_score": 0.0}

    conf = np.array(confidences)
    acc = np.array(accuracies)

    # Brier Score: mean squared error between confidence and accuracy outcome
    brier = float(np.mean((conf - acc) ** 2))

    # ECE computation
    bins = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0
    total_n = len(conf)

    for i in range(num_bins):
        bin_lower = bins[i]
        bin_upper = bins[i + 1]

        if i == num_bins - 1:
            indices = np.where((conf >= bin_lower) & (conf <= bin_upper))[0]
        else:
            indices = np.where((conf >= bin_lower) & (conf < bin_upper))[0]

        if len(indices) > 0:
            bin_acc = np.mean(acc[indices])
            bin_conf = np.mean(conf[indices])
            ece += (len(indices) / total_n) * abs(bin_acc - bin_conf)

    return {
        "ece": round(float(ece), 4),
        "brier_score": round(float(brier), 4),
    }


def compute_abstention_metrics(
    y_true: List[str],
    y_pred: List[str],
    abstention_label: str = "INSUFFICIENT_EVIDENCE",
) -> Dict[str, float]:
    """Evaluate abstention behavior: coverage and selective accuracy."""
    total = len(y_true)
    if total == 0:
        return {"coverage": 0.0, "selective_accuracy": 0.0, "overall_accuracy": 0.0}

    # Covered instances are those where model made a definitive claim (did not abstain)
    covered_indices = [i for i, p in enumerate(y_pred) if p != abstention_label]
    coverage = len(covered_indices) / total

    if covered_indices:
        covered_correct = sum(1 for i in covered_indices if y_pred[i] == y_true[i])
        selective_acc = covered_correct / len(covered_indices)
    else:
        selective_acc = 0.0

    overall_acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / total

    return {
        "coverage": round(float(coverage), 4),
        "selective_accuracy": round(float(selective_acc), 4),
        "overall_accuracy": round(float(overall_acc), 4),
        "covered_count": len(covered_indices),
        "abstained_count": total - len(covered_indices),
        "total_count": total,
    }

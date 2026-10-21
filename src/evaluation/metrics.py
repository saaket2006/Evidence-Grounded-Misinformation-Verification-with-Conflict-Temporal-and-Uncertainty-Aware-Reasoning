"""Evaluation metrics for verification, retrieval, uncertainty calibration, and abstention."""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix as sklearn_confusion_matrix, precision_recall_fscore_support

CANONICAL_LABELS = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]


def compute_verification_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute Accuracy, Macro-F1, Precision, Recall, and Confusion Matrix across 3 classes."""
    canonical_labels = labels or CANONICAL_LABELS

    if not y_true or not y_pred:
        return {
            "accuracy": 0.0,
            "macro_f1": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "confusion_matrix": [[0] * len(canonical_labels) for _ in canonical_labels],
            "labels": canonical_labels,
            "per_class": {
                lbl: {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0}
                for lbl in canonical_labels
            },
            "total_evaluated": 0,
        }

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=canonical_labels, average="macro", zero_division=0
    )

    per_class_p, per_class_r, per_class_f1, per_class_support = precision_recall_fscore_support(
        y_true, y_pred, labels=canonical_labels, average=None, zero_division=0
    )

    cm = sklearn_confusion_matrix(y_true, y_pred, labels=canonical_labels)

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
        "confusion_matrix": cm.tolist(),
        "labels": canonical_labels,
        "per_class": per_class,
        "total_evaluated": len(y_true),
    }


def compute_retrieval_metrics(
    gold_ids_list: List[Union[List[str], List[List[str]]]],
    retrieved_ids_list: List[List[str]],
    k: int = 5,
) -> Dict[str, float]:
    """Compute Recall@k, Precision@k, and MRR for evidence retrieval.

    Supports both single gold evidence lists and multiple acceptable evidence sets
    (e.g., in FEVER where a claim may have alternative corroborating sets).
    """
    if not gold_ids_list or not retrieved_ids_list:
        return {f"recall@{k}": 0.0, f"precision@{k}": 0.0, "mrr": 0.0}

    recalls = []
    precisions = []
    reciprocal_ranks = []

    for gold_raw, retrieved in zip(gold_ids_list, retrieved_ids_list):
        if not gold_raw:
            continue

        # Normalize to list of alternative evidence sets
        if len(gold_raw) > 0 and isinstance(gold_raw[0], (list, tuple, set)):
            candidate_gold_sets = [set(s) for s in gold_raw if s]
        else:
            candidate_gold_sets = [set(gold_raw)]

        if not candidate_gold_sets or not any(candidate_gold_sets):
            continue

        top_k = retrieved[:k]
        top_k_set = set(top_k)

        # For alternative evidence sets, evaluate against best matching set
        best_recall = 0.0
        best_prec = 0.0
        for gold_set in candidate_gold_sets:
            if not gold_set:
                continue
            hits = len(top_k_set & gold_set)
            rec = hits / len(gold_set)
            prec = hits / max(1, len(top_k))
            if rec > best_recall:
                best_recall = rec
                best_prec = prec
            elif rec == best_recall and prec > best_prec:
                best_prec = prec

        recalls.append(best_recall)
        precisions.append(best_prec)

        # Reciprocal Rank: rank of first gold document retrieved
        all_gold_union = set().union(*candidate_gold_sets)
        rr = 0.0
        for rank, doc_id in enumerate(top_k, 1):
            if doc_id in all_gold_union:
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
    accuracies: Optional[List[int]] = None,
    num_bins: int = 5,
    y_true: Optional[List[str]] = None,
    prob_vectors: Optional[List[List[float]]] = None,
    labels: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Compute Expected Calibration Error (ECE) and Brier Score.

    Supports both:
    1. Multiclass Brier score: when y_true and prob_vectors are provided.
       BS = (1/N) * sum_i sum_k (p_{i,k} - y_{i,k})^2
    2. Top-label calibration (ECE): binning predicted max confidence against accuracy.
    """
    if not confidences:
        return {
            "ece": 0.0,
            "brier_score": 0.0,
            "multiclass_brier": 0.0,
            "normalized_brier": 0.0,
        }

    conf = np.array(confidences)
    total_n = len(conf)

    # 1. Expected Calibration Error (ECE)
    bins = np.linspace(0.0, 1.0, num_bins + 1)
    ece = 0.0

    if accuracies is not None and len(accuracies) == total_n:
        acc = np.array(accuracies)
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

    # 2. Multiclass Brier Score
    canonical_labels = labels or CANONICAL_LABELS
    num_classes = len(canonical_labels)

    if y_true is not None and prob_vectors is not None and len(y_true) == len(prob_vectors):
        label_to_idx = {l: i for i, l in enumerate(canonical_labels)}
        brier_sum = 0.0

        for true_label, p_vec in zip(y_true, prob_vectors):
            y_one_hot = np.zeros(num_classes)
            if true_label in label_to_idx:
                y_one_hot[label_to_idx[true_label]] = 1.0
            p_arr = np.array(p_vec[:num_classes])
            # Ensure probability vector sums to 1
            if p_arr.sum() > 0:
                p_arr = p_arr / p_arr.sum()
            brier_sum += np.sum((p_arr - y_one_hot) ** 2)

        raw_multiclass_brier = float(brier_sum / max(1, len(y_true)))
        # Normalized Brier in [0, 1] by dividing by 2.0 (maximum possible squared difference per sample is 2.0)
        norm_brier = float(raw_multiclass_brier / 2.0)
        top_label_brier = float(np.mean((conf - acc) ** 2)) if accuracies is not None else raw_multiclass_brier
    else:
        # Fallback to binary top-label Brier score if probability vectors not supplied
        if accuracies is not None and len(accuracies) == total_n:
            acc = np.array(accuracies)
            top_label_brier = float(np.mean((conf - acc) ** 2))
        else:
            top_label_brier = 0.0
        raw_multiclass_brier = top_label_brier
        norm_brier = top_label_brier

    return {
        "ece": round(float(ece), 4),
        "brier_score": round(float(raw_multiclass_brier), 4),
        "multiclass_brier": round(float(raw_multiclass_brier), 4),
        "normalized_brier": round(float(norm_brier), 4),
    }


def compute_abstention_metrics(
    y_true: List[str],
    y_pred: List[str],
    abstention_label: str = "INSUFFICIENT_EVIDENCE",
) -> Dict[str, float]:
    """Evaluate abstention behavior: coverage, selective accuracy, and selective risk."""
    total = len(y_true)
    if total == 0:
        return {
            "coverage": 0.0,
            "selective_accuracy": 0.0,
            "selective_risk": 0.0,
            "overall_accuracy": 0.0,
            "covered_count": 0,
            "abstained_count": 0,
            "total_count": 0,
        }

    # Covered instances: predictions where model committed to a definitive verdict
    covered_indices = [i for i, p in enumerate(y_pred) if p != abstention_label]
    coverage = len(covered_indices) / total

    if covered_indices:
        covered_correct = sum(1 for i in covered_indices if y_pred[i] == y_true[i])
        selective_acc = covered_correct / len(covered_indices)
        selective_risk = 1.0 - selective_acc
    else:
        selective_acc = 0.0
        selective_risk = 0.0

    overall_acc = sum(1 for t, p in zip(y_true, y_pred) if t == p) / total

    return {
        "coverage": round(float(coverage), 4),
        "selective_accuracy": round(float(selective_acc), 4),
        "selective_risk": round(float(selective_risk), 4),
        "overall_accuracy": round(float(overall_acc), 4),
        "covered_count": len(covered_indices),
        "abstained_count": total - len(covered_indices),
        "total_count": total,
    }

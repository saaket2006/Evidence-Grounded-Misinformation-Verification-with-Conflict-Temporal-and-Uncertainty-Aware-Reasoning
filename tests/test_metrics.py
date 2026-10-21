"""Unit tests for evaluation metrics: classification, retrieval, calibration, and abstention."""

import pytest
import numpy as np
from src.evaluation.metrics import (
    compute_abstention_metrics,
    compute_calibration_metrics,
    compute_retrieval_metrics,
    compute_verification_metrics,
    CANONICAL_LABELS,
)


def test_verification_metrics_perfect():
    y_true = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
    y_pred = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
    res = compute_verification_metrics(y_true, y_pred)
    assert res["accuracy"] == 1.0
    assert res["macro_f1"] == 1.0
    assert res["macro_precision"] == 1.0
    assert res["macro_recall"] == 1.0
    assert res["confusion_matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    assert res["total_evaluated"] == 3


def test_verification_metrics_all_wrong():
    y_true = ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
    y_pred = ["CONTRADICTED", "INSUFFICIENT_EVIDENCE", "SUPPORTED"]
    res = compute_verification_metrics(y_true, y_pred)
    assert res["accuracy"] == 0.0
    assert res["macro_f1"] == 0.0
    assert res["confusion_matrix"] == [[0, 1, 0], [0, 0, 1], [1, 0, 0]]


def test_verification_metrics_missing_classes_in_sample():
    # Only 2 of 3 classes present in predictions
    y_true = ["SUPPORTED", "SUPPORTED", "CONTRADICTED"]
    y_pred = ["SUPPORTED", "CONTRADICTED", "CONTRADICTED"]
    res = compute_verification_metrics(y_true, y_pred)
    # Accuracy: 2 / 3 = 0.6667
    assert res["accuracy"] == 0.6667
    # SUPPORTED: P=1/1=1.0, R=1/2=0.5, F1=2*(1*0.5)/(1+0.5)=0.6667
    # CONTRADICTED: P=1/2=0.5, R=1/1=1.0, F1=0.6667
    # INSUFFICIENT_EVIDENCE: P=0, R=0, F1=0, support=0
    # Macro F1: (0.6667 + 0.6667 + 0.0) / 3 = 0.4444
    assert res["macro_f1"] == 0.4444


def test_verification_metrics_empty():
    res = compute_verification_metrics([], [])
    assert res["accuracy"] == 0.0
    assert res["total_evaluated"] == 0
    assert len(res["confusion_matrix"]) == 3


def test_retrieval_metrics_exact_hit():
    gold = [["doc_1"], ["doc_2", "doc_3"]]
    retrieved = [["doc_1", "doc_x"], ["doc_3", "doc_2", "doc_y"]]
    res = compute_retrieval_metrics(gold, retrieved, k=2)
    # Query 1: gold has doc_1. top_2 has doc_1 -> recall=1.0, prec=0.5, rank=1 -> rr=1.0
    # Query 2: gold has doc_2, doc_3. top_2 has doc_3, doc_2 -> recall=2/2=1.0, prec=2/2=1.0, rank=1 -> rr=1.0
    assert res["recall@2"] == 1.0
    assert res["precision@2"] == 0.75
    assert res["mrr"] == 1.0


def test_retrieval_metrics_miss():
    gold = [["doc_1"]]
    retrieved = [["doc_a", "doc_b", "doc_c"]]
    res = compute_retrieval_metrics(gold, retrieved, k=3)
    assert res["recall@3"] == 0.0
    assert res["precision@3"] == 0.0
    assert res["mrr"] == 0.0


def test_retrieval_metrics_multiple_acceptable_sets():
    # In FEVER, alternative evidence sets can exist: either set [doc_1] OR set [doc_2, doc_3]
    gold = [[["doc_1"], ["doc_2", "doc_3"]]]
    retrieved = [["doc_2", "doc_3", "doc_other"]]
    res = compute_retrieval_metrics(gold, retrieved, k=2)
    # Matches set 2 perfectly: recall=1.0, prec=1.0, MRR=1.0
    assert res["recall@2"] == 1.0
    assert res["precision@2"] == 1.0
    assert res["mrr"] == 1.0


def test_calibration_metrics_multiclass_perfect():
    y_true = ["SUPPORTED", "CONTRADICTED"]
    # Perfect probability vectors for ["SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
    probs = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]
    confidences = [1.0, 1.0]
    accuracies = [1, 1]
    res = compute_calibration_metrics(
        confidences=confidences,
        accuracies=accuracies,
        y_true=y_true,
        prob_vectors=probs,
    )
    # Perfect prediction has Brier score = 0.0
    assert res["multiclass_brier"] == 0.0
    assert res["normalized_brier"] == 0.0
    assert res["ece"] == 0.0


def test_calibration_metrics_multiclass_uniform_uncertainty():
    # 2 samples, uniform predictions [1/3, 1/3, 1/3]
    y_true = ["SUPPORTED", "CONTRADICTED"]
    probs = [
        [1/3, 1/3, 1/3],
        [1/3, 1/3, 1/3],
    ]
    # For one sample: true is [1, 0, 0]. Error is (1/3 - 1)^2 + (1/3 - 0)^2 + (1/3 - 0)^2 = 4/9 + 1/9 + 1/9 = 6/9 = 2/3 = 0.6667
    res = compute_calibration_metrics(
        confidences=[0.3333, 0.3333],
        accuracies=[1, 0],
        y_true=y_true,
        prob_vectors=probs,
    )
    assert abs(res["multiclass_brier"] - 0.6667) < 1e-3
    assert abs(res["normalized_brier"] - 0.3333) < 1e-3


def test_calibration_metrics_ece_manual_bins():
    # 4 samples with explicit confidences and accuracies
    conf = [0.1, 0.3, 0.7, 0.9]
    acc = [0, 0, 1, 1]
    # With 2 bins [0.0, 0.5) and [0.5, 1.0]:
    # Bin 1: conf in [0, 0.5) -> [0.1, 0.3], count=2, mean_conf=0.2, mean_acc=0.0 -> error = |0 - 0.2| = 0.2
    # Bin 2: conf in [0.5, 1.0] -> [0.7, 0.9], count=2, mean_conf=0.8, mean_acc=1.0 -> error = |1 - 0.8| = 0.2
    # ECE = (2/4)*0.2 + (2/4)*0.2 = 0.2
    res = compute_calibration_metrics(confidences=conf, accuracies=acc, num_bins=2)
    assert res["ece"] == 0.2


def test_abstention_metrics_partial_coverage():
    y_true = ["SUPPORTED", "CONTRADICTED", "SUPPORTED", "INSUFFICIENT_EVIDENCE"]
    y_pred = ["SUPPORTED", "CONTRADICTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"]
    res = compute_abstention_metrics(y_true, y_pred)
    # Total = 4
    # Non-abstaining (covered): first 3 items (count=3) -> Coverage = 3/4 = 0.75
    # Covered predictions: ["SUPPORTED", "CONTRADICTED", "CONTRADICTED"]
    # Covered true: ["SUPPORTED", "CONTRADICTED", "SUPPORTED"]
    # Covered correct: 2/3 = 0.6667 -> Selective Accuracy = 0.6667
    # Selective Risk: 1 - 0.6667 = 0.3333
    # Overall Accuracy: items 0, 1, 3 match -> 3/4 = 0.75
    assert res["coverage"] == 0.75
    assert res["selective_accuracy"] == 0.6667
    assert res["selective_risk"] == 0.3333
    assert res["overall_accuracy"] == 0.75
    assert res["covered_count"] == 3
    assert res["abstained_count"] == 1


def test_abstention_metrics_zero_coverage():
    y_true = ["SUPPORTED", "CONTRADICTED"]
    y_pred = ["INSUFFICIENT_EVIDENCE", "INSUFFICIENT_EVIDENCE"]
    res = compute_abstention_metrics(y_true, y_pred)
    assert res["coverage"] == 0.0
    assert res["selective_accuracy"] == 0.0
    assert res["selective_risk"] == 0.0
    assert res["overall_accuracy"] == 0.0
    assert res["abstained_count"] == 2

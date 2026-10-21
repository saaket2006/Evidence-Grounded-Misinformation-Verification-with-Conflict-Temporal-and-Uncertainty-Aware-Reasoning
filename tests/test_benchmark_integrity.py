"""Regression tests for benchmark integrity:
1. Experiment E missing results / explicit N/A handling (preventing metric inheritance).
2. Evidence-set representation: multi-hop conjunctive sets, alternative disjunctive sets, and NEI claims.
3. Test selection independence: ensuring test claims are sampled independently of corpus coverage.
"""

import json
from pathlib import Path
import pytest

from src.evaluation.metrics import compute_retrieval_metrics, compute_verification_metrics


def test_experiment_e_explicit_na_in_results():
    """Verify Experiment E result file has explicit nulls/NOT_EVALUATED and no inherited metrics."""
    result_path = Path("results/llm_assisted.json")
    if not result_path.exists():
        pytest.skip("results/llm_assisted.json does not exist yet.")

    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("llm_status") == "NOT_EVALUATED"
    assert data.get("verification_metrics") is None
    assert data.get("retrieval_metrics") is None
    assert data.get("calibration_metrics") is None
    assert data.get("abstention_metrics") is None
    assert "unevaluated" in data.get("note", "").lower()


def test_experiment_e_no_inheritance_in_summary_table():
    """Verify Experiment E row in summary_table.csv and summary_table.json has explicit 'N/A'."""
    csv_path = Path("results/summary_table.csv")
    json_path = Path("results/summary_table.json")
    if not csv_path.exists() or not json_path.exists():
        pytest.skip("Summary tables do not exist yet.")

    with open(json_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    exp_e_rows = [r for r in rows if "Experiment E" in r["Experiment"]]
    assert len(exp_e_rows) == 1, "Experiment E should appear in summary table."
    exp_e = exp_e_rows[0]

    # Verify all metric fields are explicit 'N/A' string, NOT numbers inherited from D
    for metric_col in ["Accuracy", "Macro-F1", "Recall@5", "MRR", "ECE", "Coverage", "Selective Acc"]:
        assert exp_e[metric_col] == "N/A", f"Experiment E {metric_col} must be 'N/A', found {exp_e[metric_col]}"


def test_retrieval_metrics_conjunctive_multihop():
    """Verify conjunctive multi-hop evidence requires all documents for full recall."""
    # Claim requires BOTH doc_A and doc_B
    gold_ids = [[["doc_A", "doc_B"]]]

    # Case 1: Only doc_A retrieved
    retrieved_partial = [["doc_A", "doc_X", "doc_Y"]]
    metrics_partial = compute_retrieval_metrics(gold_ids, retrieved_partial, k=3)
    assert metrics_partial["recall@3"] == 0.5
    assert metrics_partial["mrr"] == 1.0  # first hit at rank 1

    # Case 2: Both doc_A and doc_B retrieved
    retrieved_full = [["doc_A", "doc_B", "doc_X"]]
    metrics_full = compute_retrieval_metrics(gold_ids, retrieved_full, k=3)
    assert metrics_full["recall@3"] == 1.0
    assert metrics_full["mrr"] == 1.0

    # Case 3: Neither retrieved (e.g. out of corpus)
    retrieved_none = [["doc_X", "doc_Y", "doc_Z"]]
    metrics_none = compute_retrieval_metrics(gold_ids, retrieved_none, k=3)
    assert metrics_none["recall@3"] == 0.0
    assert metrics_none["mrr"] == 0.0


def test_retrieval_metrics_alternative_evidence_sets():
    """Verify disjunctive alternative evidence sets (either set satisfies claim)."""
    # Alternative set 1: [doc_A] OR Alternative set 2: [doc_B, doc_C]
    gold_ids = [[["doc_A"], ["doc_B", "doc_C"]]]

    # Retrieving doc_B and doc_C satisfies alternative set 2 completely
    retrieved = [["doc_B", "doc_C", "doc_Z"]]
    metrics = compute_retrieval_metrics(gold_ids, retrieved, k=3)
    assert metrics["recall@3"] == 1.0
    assert metrics["precision@3"] == round(2 / 3, 4)
    assert metrics["mrr"] == 1.0


def test_retrieval_metrics_nei_claims_ignored():
    """Verify NOT ENOUGH INFO / empty evidence sets do not skew retrieval recall denominator."""
    gold_ids = [
        [["doc_A"]],  # Verifiable claim
        [],           # NEI claim (no evidence)
        [],           # NEI claim (no evidence)
    ]
    retrieved = [
        ["doc_A", "doc_B"],
        ["doc_C", "doc_D"],
        ["doc_E", "doc_F"],
    ]
    metrics = compute_retrieval_metrics(gold_ids, retrieved, k=2)
    # Only the first claim should be evaluated (1 hit out of 1 verifiable claim = recall 1.0)
    assert metrics["recall@2"] == 1.0
    assert metrics["mrr"] == 1.0


def test_held_out_test_independent_of_corpus_coverage():
    """Verify that test split contains claims whose gold evidence is NOT in the corpus (no selection bias)."""
    test_path = Path("data/processed/test.jsonl")
    corpus_path = Path("data/processed/corpus.jsonl")
    info_path = Path("data/processed/dataset_info.json")

    assert test_path.exists(), "test.jsonl must exist"
    assert corpus_path.exists(), "corpus.jsonl must exist"
    assert info_path.exists(), "dataset_info.json must exist"

    with open(test_path, "r", encoding="utf-8") as f:
        test_claims = [json.loads(line) for line in f]

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_docs = [json.loads(line) for line in f]
    corpus_doc_ids = {doc["id"] for doc in corpus_docs}

    with open(info_path, "r", encoding="utf-8") as f:
        dataset_info = json.load(f)

    # 1. Total claims must be 60 with balanced 20/20/20 labels
    assert len(test_claims) == 60
    labels = [c["label"] for c in test_claims]
    assert labels.count("SUPPORTED") == 20
    assert labels.count("CONTRADICTED") == 20
    assert labels.count("INSUFFICIENT_EVIDENCE") == 20

    # 2. NEI claims must have empty evidence sets
    for c in test_claims:
        if c["label"] == "INSUFFICIENT_EVIDENCE":
            assert c.get("evidence_sets") == []

    # 3. Check evidence coverage in the 100-doc corpus
    unrepresented_claims = 0
    complete_claims = 0
    for c in test_claims:
        ev_sets = c.get("evidence_sets", [])
        if not ev_sets:
            continue
        has_complete = any(all(doc_id in corpus_doc_ids for doc_id in s) for s in ev_sets)
        if has_complete:
            complete_claims += 1
        else:
            unrepresented_claims += 1

    # In unbiased sampling, most claims should NOT have their gold evidence in the 100-doc corpus
    assert unrepresented_claims > 0, "Unbiased test set must contain claims with evidence outside the corpus!"
    assert unrepresented_claims > complete_claims, "Corpus of 100 docs cannot cover the majority of random FEVER dev claims."

    # 4. Check dataset_info.json records exact coverage
    test_coverage = dataset_info.get("evidence_coverage", {}).get("test", {})
    assert "SUPPORTED" in test_coverage
    assert "CONTRADICTED" in test_coverage
    assert "INSUFFICIENT_EVIDENCE" in test_coverage
    assert test_coverage["CONTRADICTED"]["complete_evidence_in_corpus"] > 0
    assert test_coverage["CONTRADICTED"]["no_evidence_in_corpus"] > 0

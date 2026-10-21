"""Run the full benchmark experimental suite (Experiments A, B, C, D, E).

Outputs machine-readable JSON and CSV results comparing each configuration.
"""

import argparse
import copy
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List
import pandas as pd

# Ensure project root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.metrics import (
    compute_abstention_metrics,
    compute_calibration_metrics,
    compute_retrieval_metrics,
    compute_verification_metrics,
)
from src.pipeline.verifier import MisinformationVerifier
from src.utils.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


EXPERIMENT_CONFIGS = {
    "baseline": {
        "name": "Experiment A: Baseline Direct Classifier",
        "file": "baseline.json",
        "overrides": {
            "claim_processing": {"enable_decomposition": False},
            "retrieval": {"enabled": False},
            "reranking": {"enabled": False},
            "conflict": {"enabled": False},
            "temporal": {"enabled": False},
            "uncertainty": {"enabled": False},
            "experiments": {"use_abstention": False},
            "reasoning": {"llm_enabled": False},
        },
    },
    "evidence_aware": {
        "name": "Experiment B: Evidence-Aware (Retrieval + NLI)",
        "file": "evidence_aware.json",
        "overrides": {
            "claim_processing": {"enable_decomposition": False},
            "retrieval": {"enabled": True},
            "reranking": {"enabled": True},
            "conflict": {"enabled": False},
            "temporal": {"enabled": False},
            "uncertainty": {"enabled": False},
            "experiments": {"use_abstention": False},
            "reasoning": {"llm_enabled": False},
        },
    },
    "temporal_conflict": {
        "name": "Experiment C: Conflict- & Temporal-Aware",
        "file": "temporal_conflict.json",
        "overrides": {
            "claim_processing": {"enable_decomposition": True},
            "retrieval": {"enabled": True},
            "reranking": {"enabled": True},
            "conflict": {"enabled": True},
            "temporal": {"enabled": True},
            "uncertainty": {"enabled": False},
            "experiments": {"use_abstention": False},
            "reasoning": {"llm_enabled": False},
        },
    },
    "full_system": {
        "name": "Experiment D: Full Proposed System (with Uncertainty & Abstention)",
        "file": "full_system.json",
        "overrides": {
            "claim_processing": {"enable_decomposition": True},
            "retrieval": {"enabled": True},
            "reranking": {"enabled": True},
            "conflict": {"enabled": True},
            "temporal": {"enabled": True},
            "uncertainty": {"enabled": True},
            "experiments": {"use_abstention": True},
            "reasoning": {"llm_enabled": False},
        },
    },
    "llm_assisted": {
        "name": "Experiment E: Full System + LLM Reasoning Advisor",
        "file": "llm_assisted.json",
        "overrides": {
            "claim_processing": {"enable_decomposition": True},
            "retrieval": {"enabled": True},
            "reranking": {"enabled": True},
            "conflict": {"enabled": True},
            "temporal": {"enabled": True},
            "uncertainty": {"enabled": True},
            "experiments": {"use_abstention": True},
            "reasoning": {"llm_enabled": True},
        },
    },
}


def load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL dataset split."""
    data = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def run_experiment(
    exp_key: str,
    base_config: Dict[str, Any],
    dataset: List[Dict[str, Any]],
    results_dir: Path,
) -> Dict[str, Any]:
    exp_def = EXPERIMENT_CONFIGS[exp_key]
    logger.info(f"\n==========================================")
    logger.info(f"Running {exp_def['name']}...")
    logger.info(f"==========================================")

    # Merge configuration
    from src.utils.config import merge_configs
    cfg = merge_configs(base_config, exp_def["overrides"])

    # Instantiate pipeline with this configuration
    verifier = MisinformationVerifier(config=cfg)

    y_true: List[str] = []
    y_pred: List[str] = []
    confidences: List[float] = []
    accuracies: List[int] = []
    prob_vectors: List[List[float]] = []
    gold_ids: List[List[str]] = []
    retrieved_ids: List[List[str]] = []
    item_details: List[Dict[str, Any]] = []
    llm_actually_executed_count = 0

    for item in dataset:
        claim_text = item["claim"]
        true_label = item["label"]
        # Preserve FEVER's alternative acceptable evidence sets and multi-hop structure
        gold_ev = item.get("evidence_sets")
        if gold_ev is None:
            # Fallback for datasets with simple flattened evidence_ids
            raw_ids = item.get("evidence_ids", [])
            gold_ev = [raw_ids] if raw_ids else []

        res = verifier.verify(claim_text)
        pred_label = res.verdict.value
        conf = res.confidence

        is_correct = 1 if pred_label == true_label else 0
        y_true.append(true_label)
        y_pred.append(pred_label)
        confidences.append(conf)
        accuracies.append(is_correct)

        # Extract 3-class probability distribution
        agg_meta = res.metadata.get("aggregation", {})
        p_sup = float(agg_meta.get("support_prob", 0.0))
        p_con = float(agg_meta.get("contradict_prob", 0.0))
        p_neu = float(agg_meta.get("neutral_prob", 0.0))
        prob_vectors.append([p_sup, p_con, p_neu])

        # Track genuine LLM execution
        advice_flags = res.metadata.get("reasoning", {}).get("flags", [])
        if "LLM_STRUCTURED_RESPONSE" in advice_flags or "LLM_RAW_TEXT_RESPONSE" in advice_flags:
            llm_actually_executed_count += 1

        ret_ev = [p.id for p in res.evidence]
        gold_ids.append(gold_ev)
        retrieved_ids.append(ret_ev)

        item_details.append({
            "id": item.get("id"),
            "claim": claim_text,
            "true_label": true_label,
            "pred_label": pred_label,
            "correct": bool(is_correct),
            "confidence": conf,
            "uncertainty": res.uncertainty,
            "conflict_detected": res.conflict_detected,
            "reasoning": res.reasoning,
        })

    # Compute evaluation metrics
    verif_metrics = compute_verification_metrics(y_true, y_pred)
    retrieval_metrics = compute_retrieval_metrics(gold_ids, retrieved_ids, k=5)
    calib_metrics = compute_calibration_metrics(
        confidences=confidences,
        accuracies=accuracies,
        y_true=y_true,
        prob_vectors=prob_vectors,
    )
    abstention_metrics = compute_abstention_metrics(y_true, y_pred)

    is_llm_experiment = (exp_key == "llm_assisted")
    llm_status = "EXECUTED" if (is_llm_experiment and llm_actually_executed_count > 0) else ("NOT_EVALUATED" if is_llm_experiment else "N/A")

    result_payload = {
        "experiment_key": exp_key,
        "name": exp_def["name"],
        "num_claims": len(dataset),
        "llm_status": llm_status,
        "llm_calls_succeeded": llm_actually_executed_count,
        "verification_metrics": verif_metrics,
        "retrieval_metrics": retrieval_metrics,
        "calibration_metrics": calib_metrics,
        "abstention_metrics": abstention_metrics,
        "claims_evaluated": item_details,
    }

    # Save to results/
    out_file = results_dir / exp_def["file"]
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result_payload, f, indent=2)
    logger.info(f"Saved results to {out_file}")

    return result_payload


def main():
    parser = argparse.ArgumentParser(description="Run benchmark experiment suite")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Base config path")
    parser.add_argument("--dataset", type=str, default="data/processed/test.jsonl", help="Test dataset path")
    parser.add_argument("--results_dir", type=str, default="results", help="Directory to save results")
    parser.add_argument("--experiments", nargs="+", default=["baseline", "evidence_aware", "temporal_conflict", "full_system", "llm_assisted"], help="Experiments to run")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    base_config = load_config(args.config)
    dataset = load_dataset(Path(args.dataset))
    logger.info(f"Loaded {len(dataset)} evaluation items from {args.dataset}")

    all_results = []
    summary_rows = []

    for exp_key in args.experiments:
        if exp_key in EXPERIMENT_CONFIGS:
            res = run_experiment(exp_key, base_config, dataset, results_dir)
            all_results.append(res)

            v = res["verification_metrics"]
            r = res["retrieval_metrics"]
            c = res["calibration_metrics"]
            a = res["abstention_metrics"]

            exp_name = res["name"]
            if res.get("llm_status") == "NOT_EVALUATED":
                exp_name += " [NOT EVALUATED - No API Key]"

            summary_rows.append({
                "Experiment": exp_name,
                "Accuracy": v["accuracy"],
                "Macro-F1": v["macro_f1"],
                "Recall@5": r.get("recall@5", 0.0),
                "MRR": r.get("mrr", 0.0),
                "ECE": c["ece"],
                "Brier (MC)": c.get("multiclass_brier", c.get("brier_score")),
                "Coverage": a["coverage"],
                "Selective Acc": a["selective_accuracy"],
            })

    # Save summary table
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(results_dir / "summary_table.csv", index=False)
    with open(results_dir / "summary_table.json", "w", encoding="utf-8") as f:
        json.dump(summary_rows, f, indent=2)

    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK EXPERIMENTS SUMMARY:")
    logger.info("=" * 60)
    logger.info("\n" + summary_df.to_string(index=False))


if __name__ == "__main__":
    main()

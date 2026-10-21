"""Run standalone evaluation on a dataset split and export metrics."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.metrics import (
    compute_abstention_metrics,
    compute_calibration_metrics,
    compute_retrieval_metrics,
    compute_verification_metrics,
)
from src.pipeline.verifier import MisinformationVerifier


def evaluate(config_path: str, dataset_path: str, output_path: str) -> None:
    verifier = MisinformationVerifier(config_path=config_path)

    claims = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                claims.append(json.loads(line))

    y_true = []
    y_pred = []
    confidences = []
    accuracies = []
    gold_ids = []
    retrieved_ids = []

    for item in claims:
        claim_text = item["claim"]
        true_label = item["label"]
        res = verifier.verify(claim_text)

        y_true.append(true_label)
        y_pred.append(res.verdict.value)
        confidences.append(res.confidence)
        accuracies.append(1 if res.verdict.value == true_label else 0)
        gold_ids.append(item.get("evidence_ids", []))
        retrieved_ids.append([p.id for p in res.evidence])

    metrics = {
        "verification": compute_verification_metrics(y_true, y_pred),
        "retrieval": compute_retrieval_metrics(gold_ids, retrieved_ids, k=5),
        "calibration": compute_calibration_metrics(confidences, accuracies),
        "abstention": compute_abstention_metrics(y_true, y_pred),
    }

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Evaluate verification system")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Config file")
    parser.add_argument("--dataset", type=str, default="data/processed/dev.jsonl", help="Dataset path")
    parser.add_argument("--output", type=str, default="results/evaluation.json", help="Output path")
    args = parser.parse_args()
    evaluate(args.config, args.dataset, args.output)


if __name__ == "__main__":
    main()

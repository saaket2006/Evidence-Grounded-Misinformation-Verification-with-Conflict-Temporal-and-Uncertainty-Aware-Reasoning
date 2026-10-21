"""Script to verify and inspect representative end-to-end claims across all scenarios:
1. Supported claim (Authentic FEVER)
2. Contradicted claim (Authentic FEVER)
3. Insufficient evidence claim (Authentic FEVER / OOD)
4. Compound claim (Decomposition into subclaims)
5. Conflicting evidence claim (Controlled scenario)
6. Time-sensitive claim (Controlled scenario)
"""

import json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.verifier import MisinformationVerifier


def run_representative_inspections():
    results_summary = []

    # 1. Standard pipeline with authentic FEVER corpus
    print("=" * 80)
    print("INITIALIZING VERIFIER (Default FEVER Corpus)...")
    print("=" * 80)
    verifier_fever = MisinformationVerifier(config_path="configs/default.yaml")

    fever_claims = [
        ("SUPPORTED", "Fox 2000 Pictures released the film Soul Food."),
        ("CONTRADICTED", "Telemundo is a English-language television network."),
        ("INSUFFICIENT_EVIDENCE", "The ancient lost civilization of Atlantis was powered by crystal energy."),
        ("COMPOUND", "Fox 2000 Pictures released the film Soul Food, and Telemundo is an English-language television network.")
    ]

    for category, claim in fever_claims:
        print("\n" + "-" * 70)
        print(f"CATEGORY: {category}")
        print(f"CLAIM:    {claim}")
        res = verifier_fever.verify(claim)
        print(f"VERDICT:            {res.verdict.value}")
        print(f"CONFIDENCE:         {res.confidence:.4f}")
        print(f"UNCERTAINTY:        {res.uncertainty:.4f}")
        print(f"CONFLICT DETECTED:  {res.conflict_detected}")
        is_abstained = (res.verdict.value == "INSUFFICIENT_EVIDENCE")
        abstention_reason = res.reasoning if is_abstained else "N/A"
        print(f"ABSTAINED:          {is_abstained} (reason: {abstention_reason})")
        if res.subclaims and len(res.subclaims) > 1:
            print("SUBCLAIMS:")
            for sc in res.subclaims:
                print(f"  - [{sc.verdict.value if sc.verdict else 'N/A'}] {sc.text}")
        print("TOP EVIDENCE:")
        for idx, ev in enumerate(res.evidence[:3], 1):
            nli = ev.nli_label.value if ev.nli_label else "N/A"
            print(f"  [{idx}] {ev.source} (NLI: {nli}, score: {ev.nli_score}, retr: {ev.retrieval_score:.4f})")
            print(f"      Text: {ev.text[:120]}...")
            if ev.temporal_notes:
                print(f"      Temporal: {ev.temporal_notes}")
        print(f"EXPLANATION: {res.reasoning}")

        results_summary.append({
            "category": category,
            "claim": claim,
            "verdict": res.verdict.value,
            "confidence": res.confidence,
            "uncertainty": res.uncertainty,
            "conflict_detected": res.conflict_detected,
            "abstained": is_abstained,
            "abstention_reason": abstention_reason,
            "top_evidence_count": len(res.evidence),
            "subclaim_count": len(res.subclaims) if res.subclaims else 0
        })

    # 2. Controlled scenario pipeline with controlled corpus
    print("\n" + "=" * 80)
    print("INITIALIZING VERIFIER (Controlled Edge-Case Corpus)...")
    print("=" * 80)
    
    # Create temporary config pointing to controlled corpus
    import yaml
    with open("configs/default.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["retrieval"]["corpus_path"] = "data/controlled/corpus.jsonl"
    cfg["retrieval"]["bm25_index_path"] = None  # Rebuild in memory from controlled corpus
    cfg["retrieval"]["dense_index_path"] = None # Rebuild in memory from controlled corpus

    controlled_cfg_path = Path("configs/controlled_temp.yaml")
    with open(controlled_cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f)

    verifier_controlled = MisinformationVerifier(config_path=str(controlled_cfg_path))

    controlled_claims = [
        ("CONFLICTING_EVIDENCE", "NovaTech achieved $10 million in enterprise revenue in 2024."),
        ("TIME_SENSITIVE", "Acme Corporation is currently the global market leader in autonomous delivery drones.")
    ]

    for category, claim in controlled_claims:
        print("\n" + "-" * 70)
        print(f"CATEGORY: {category}")
        print(f"CLAIM:    {claim}")
        res = verifier_controlled.verify(claim)
        print(f"VERDICT:            {res.verdict.value}")
        print(f"CONFIDENCE:         {res.confidence:.4f}")
        print(f"UNCERTAINTY:        {res.uncertainty:.4f}")
        print(f"CONFLICT DETECTED:  {res.conflict_detected}")
        is_abstained = (res.verdict.value == "INSUFFICIENT_EVIDENCE")
        abstention_reason = res.reasoning if is_abstained else "N/A"
        print(f"ABSTAINED:          {is_abstained} (reason: {abstention_reason})")
        print("TOP EVIDENCE:")
        for idx, ev in enumerate(res.evidence[:3], 1):
            nli = ev.nli_label.value if ev.nli_label else "N/A"
            print(f"  [{idx}] {ev.source} (Date: {ev.published_date}, NLI: {nli}, score: {ev.nli_score})")
            print(f"      Text: {ev.text[:120]}...")
            if ev.temporal_notes:
                print(f"      Temporal: {ev.temporal_notes}")
        print(f"EXPLANATION: {res.reasoning}")

        results_summary.append({
            "category": category,
            "claim": claim,
            "verdict": res.verdict.value,
            "confidence": res.confidence,
            "uncertainty": res.uncertainty,
            "conflict_detected": res.conflict_detected,
            "abstained": is_abstained,
            "abstention_reason": abstention_reason,
            "top_evidence_count": len(res.evidence),
            "subclaim_count": len(res.subclaims) if res.subclaims else 0
        })

    # Cleanup temporary config
    if controlled_cfg_path.exists():
        controlled_cfg_path.unlink()

    # Save summary
    out_path = Path("results/representative_claims_audit.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
    print("\n" + "=" * 80)
    print(f"Saved representative claims audit to {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_representative_inspections()

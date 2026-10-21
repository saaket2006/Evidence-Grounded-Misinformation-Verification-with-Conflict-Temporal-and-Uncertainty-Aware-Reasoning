"""CLI entry point to verify a single claim using the verification pipeline."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.verifier import MisinformationVerifier


def main():
    parser = argparse.ArgumentParser(description="Verify a textual claim")
    parser.add_argument("claim", type=str, help="Claim statement to verify")
    parser.add_argument("--config", type=str, default="configs/default.yaml", help="Path to configuration file")
    parser.add_argument("--json", action="store_true", help="Print raw JSON output")
    args = parser.parse_args()

    verifier = MisinformationVerifier(config_path=args.config)
    result = verifier.verify(args.claim)

    if args.json:
        print(result.model_dump_json(indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"CLAIM: {result.claim}")
        print("=" * 60)
        print(f"VERDICT:            {result.verdict.value}")
        print(f"CONFIDENCE:         {result.confidence:.2%}")
        print(f"UNCERTAINTY:        {result.uncertainty:.2%}")
        print(f"CONFLICT DETECTED:  {result.conflict_detected}")
        if result.subclaims and len(result.subclaims) > 1:
            print("\nSUBCLAIMS:")
            for sc in result.subclaims:
                print(f"  - [{sc.verdict.value if sc.verdict else 'N/A'}] {sc.text}")

        print("\nTOP EVIDENCE PASSAGES:")
        if not result.evidence:
            print("  (No relevant evidence retrieved)")
        for i, ev in enumerate(result.evidence, 1):
            nli = ev.nli_label.value if ev.nli_label else "N/A"
            print(f"  [{i}] Source: {ev.source} | Date: {ev.published_date} | NLI: {nli} (score: {ev.nli_score})")
            print(f"      Text: {ev.text}")
            if ev.temporal_notes:
                print(f"      Temporal: {ev.temporal_notes}")

        print("\nEXPLANATION:")
        print(result.reasoning)
        print("=" * 60)


if __name__ == "__main__":
    main()

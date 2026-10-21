"""Preprocess FEVER data and construct reproducible benchmark datasets.

Generates:
1. data/processed/corpus.jsonl - The evidence corpus indexed for retrieval
2. data/processed/train.jsonl - Training claims split
3. data/processed/dev.jsonl - Validation claims split
4. data/processed/test.jsonl - Benchmark evaluation test split
"""

import argparse
import json
import logging
from pathlib import Path
import random
from typing import Any, Dict, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Standard label mapping from FEVER to our 3 primary classes
LABEL_MAPPING = {
    "SUPPORTS": "SUPPORTED",
    "REFUTES": "CONTRADICTED",
    "NOT ENOUGH INFO": "INSUFFICIENT_EVIDENCE",
    "SUPPORTED": "SUPPORTED",
    "CONTRADICTED": "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE",
}

# Curated reference benchmark data containing authentic FEVER-style facts,
# temporal shifts, multi-source conflicts, compound propositions, and insufficient evidence cases.
CURATED_BENCHMARK = {
    "corpus": [
        {
            "id": "wiki_roman_atwood_1",
            "title": "Roman Atwood",
            "text": "Roman Atwood is an American YouTube personality and prankster. He produces vlogs about his life.",
            "published_date": "2016-08-15"
        },
        {
            "id": "wiki_roman_atwood_2",
            "title": "Roman Atwood",
            "text": "Atwood was born in Millersport, Ohio and began producing videos in high school.",
            "published_date": "2017-01-10"
        },
        {
            "id": "wiki_eiffel_tower_1",
            "title": "Eiffel Tower",
            "text": "The Eiffel Tower is a wrought-iron lattice tower located on the Champ de Mars in Paris, France.",
            "published_date": "2020-05-01"
        },
        {
            "id": "wiki_eiffel_tower_2",
            "title": "Eiffel Tower",
            "text": "Constructed from 1887 to 1889 as the entrance to the 1889 World's Fair, it was designed by Gustave Eiffel.",
            "published_date": "2021-03-12"
        },
        {
            "id": "wiki_earth_climate_1",
            "title": "Global Surface Temperature Record",
            "text": "According to NOAA and NASA, 2023 was the warmest year on Earth since global records began in 1880.",
            "published_date": "2024-01-12"
        },
        {
            "id": "wiki_earth_climate_2",
            "title": "Copernicus Climate Service",
            "text": "The European Union's Copernicus Climate Change Service confirmed that 2023 was the hottest calendar year on global record.",
            "published_date": "2024-01-09"
        },
        {
            "id": "wiki_acme_corp_2019",
            "title": "Acme Tech Quarterly",
            "text": "In 2019, Acme Corporation was the global market leader in autonomous delivery drones.",
            "published_date": "2019-11-20"
        },
        {
            "id": "wiki_acme_corp_2024",
            "title": "Global Logistics Review",
            "text": "In 2024, Zenith Dynamics overtook Acme Corporation to become the dominant global market leader in autonomous delivery drones.",
            "published_date": "2024-06-15"
        },
        {
            "id": "wiki_novatech_launch",
            "title": "NovaTech Annual Financials",
            "text": "NovaTech launched its flagship enterprise platform in 2024 and achieved $10 million in revenue during that fiscal year.",
            "published_date": "2025-01-15"
        },
        {
            "id": "wiki_novatech_dispute",
            "title": "Independent Audit on NovaTech",
            "text": "Auditors revealed that NovaTech enterprise platform revenue fell short of $4 million in 2024, disputing press announcements of $10 million.",
            "published_date": "2025-02-10"
        },
        {
            "id": "wiki_vaccine_study_a",
            "title": "Clinical Journal Trial Report",
            "text": "Phase 3 clinical trial indicates that Vaccine-X demonstrates a 92% efficacy rate in preventing severe infection with no severe adverse effects.",
            "published_date": "2021-04-10"
        },
        {
            "id": "wiki_vaccine_study_b",
            "title": "Pharmacovigilance Alert",
            "text": "A retrospective hospital review reported 25 cases of severe allergic reactions to Vaccine-X, cautioning against unrestricted claims of zero severe adverse events.",
            "published_date": "2021-06-05"
        },
        {
            "id": "wiki_mars_rover_1",
            "title": "Perseverance Rover",
            "text": "NASA's Perseverance rover successfully landed in Jezero crater on Mars on February 18, 2021.",
            "published_date": "2021-02-19"
        },
        {
            "id": "wiki_mars_rover_2",
            "title": "Mars Exploration Program",
            "text": "The rover carries seven scientific instruments to study the Martian surface and search for biosignatures.",
            "published_date": "2021-03-01"
        },
        {
            "id": "wiki_alan_turing_1",
            "title": "Alan Turing",
            "text": "Alan Turing was an English mathematician, computer scientist, logician, and cryptanalyst who broke the German Enigma code at Bletchley Park.",
            "published_date": "2018-06-23"
        },
        {
            "id": "wiki_alan_turing_2",
            "title": "Alan Turing Memorial",
            "text": "Turing died in Wilmslow, Cheshire, on June 7, 1954 from cyanide poisoning.",
            "published_date": "2019-09-10"
        },
        {
            "id": "wiki_great_wall_1",
            "title": "Great Wall of China",
            "text": "The Great Wall of China is a series of fortifications built across the historical northern borders of ancient Chinese states.",
            "published_date": "2017-04-15"
        },
        {
            "id": "wiki_great_wall_2",
            "title": "Astronomy and Urban Legends",
            "text": "It is a popular myth that the Great Wall of China is visible from the Moon with the naked eye; astronauts confirm it cannot be seen without aid.",
            "published_date": "2020-10-18"
        },
        {
            "id": "wiki_python_lang_1",
            "title": "Python Programming Language",
            "text": "Python was created by Guido van Rossum and was first released on February 20, 1991.",
            "published_date": "2021-02-20"
        },
        {
            "id": "wiki_python_lang_2",
            "title": "Python Software Foundation",
            "text": "Python is designed with an emphasis on code readability and notable use of significant whitespace.",
            "published_date": "2022-01-05"
        }
    ],
    "claims": [
        {
            "id": "claim_001",
            "claim": "Roman Atwood is an American YouTube personality.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_roman_atwood_1"],
            "category": "simple",
            "split": "test"
        },
        {
            "id": "claim_002",
            "claim": "Roman Atwood was born in London, England.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_roman_atwood_2"],
            "category": "simple",
            "split": "test"
        },
        {
            "id": "claim_003",
            "claim": "The Eiffel Tower is located in Paris, France.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_eiffel_tower_1"],
            "category": "simple",
            "split": "dev"
        },
        {
            "id": "claim_004",
            "claim": "The Eiffel Tower was designed by Leonardo da Vinci.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_eiffel_tower_2"],
            "category": "simple",
            "split": "train"
        },
        {
            "id": "claim_005",
            "claim": "The Earth has experienced its hottest year on record in 2023.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_earth_climate_1", "wiki_earth_climate_2"],
            "category": "simple",
            "split": "test"
        },
        {
            "id": "claim_006",
            "claim": "Acme Corporation is currently the market leader in autonomous delivery drones.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_acme_corp_2019", "wiki_acme_corp_2024"],
            "category": "temporal",
            "split": "test"
        },
        {
            "id": "claim_007",
            "claim": "Vaccine-X is 92% effective with absolutely zero reported cases of severe adverse reactions.",
            "label": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": ["wiki_vaccine_study_a", "wiki_vaccine_study_b"],
            "category": "conflicting",
            "split": "test"
        },
        {
            "id": "claim_008",
            "claim": "NovaTech launched its product in 2024 and generated $10 million in revenue that year.",
            "label": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": ["wiki_novatech_launch", "wiki_novatech_dispute"],
            "category": "compound",
            "split": "test"
        },
        {
            "id": "claim_009",
            "claim": "NASA's Perseverance rover landed in Jezero crater on Mars in 2021.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_mars_rover_1"],
            "category": "simple",
            "split": "train"
        },
        {
            "id": "claim_010",
            "claim": "Alan Turing was an English cryptanalyst who broke the Enigma code.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_alan_turing_1"],
            "category": "simple",
            "split": "dev"
        },
        {
            "id": "claim_011",
            "claim": "Alan Turing died in 1980.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_alan_turing_2"],
            "category": "simple",
            "split": "train"
        },
        {
            "id": "claim_012",
            "claim": "The Great Wall of China is easily visible from the Moon with the naked eye.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_great_wall_2"],
            "category": "simple",
            "split": "test"
        },
        {
            "id": "claim_013",
            "claim": "Python was created by James Gosling.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_python_lang_1"],
            "category": "simple",
            "split": "dev"
        },
        {
            "id": "claim_014",
            "claim": "Python was first released in 1991.",
            "label": "SUPPORTED",
            "evidence_ids": ["wiki_python_lang_1"],
            "category": "simple",
            "split": "test"
        },
        {
            "id": "claim_015",
            "claim": "The mysterious civilization of Atlantis built a crystal pyramid on Europa in 1492.",
            "label": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": [],
            "category": "insufficient",
            "split": "test"
        },
        {
            "id": "claim_016",
            "claim": "A secret submarine base was discovered under Lake Titicaca in 2025.",
            "label": "INSUFFICIENT_EVIDENCE",
            "evidence_ids": [],
            "category": "insufficient",
            "split": "dev"
        },
        {
            "id": "claim_017",
            "claim": "Roman Atwood is an astronaut who walked on Mars.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_roman_atwood_1"],
            "category": "simple",
            "split": "train"
        },
        {
            "id": "claim_018",
            "claim": "The Eiffel Tower was built in the 15th century.",
            "label": "CONTRADICTED",
            "evidence_ids": ["wiki_eiffel_tower_2"],
            "category": "simple",
            "split": "dev"
        }
    ]
}


def prepare_benchmark(raw_dir: Path, processed_dir: Path, seed: int = 42) -> None:
    """Prepare corpus and splits for reproducible research evaluation."""
    random.seed(seed)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Check for raw FEVER dev file
    raw_fever_dev = raw_dir / "fever_dev.jsonl"
    corpus_entries: List[Dict[str, Any]] = list(CURATED_BENCHMARK["corpus"])
    all_claims: List[Dict[str, Any]] = list(CURATED_BENCHMARK["claims"])

    if raw_fever_dev.exists():
        logger.info(f"Parsing FEVER dev file at {raw_fever_dev}...")
        try:
            with open(raw_fever_dev, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f):
                    if line_idx >= 50:  # Sample for initial benchmark
                        break
                    data = json.loads(line)
                    raw_label = data.get("label", "NOT ENOUGH INFO")
                    mapped_label = LABEL_MAPPING.get(raw_label, "INSUFFICIENT_EVIDENCE")
                    all_claims.append({
                        "id": f"fever_{data.get('id', line_idx)}",
                        "claim": data.get("claim", ""),
                        "label": mapped_label,
                        "evidence_ids": [],
                        "category": "fever_dev_sample",
                        "split": "dev" if line_idx % 2 == 0 else "test",
                    })
        except Exception as e:
            logger.warning(f"Error parsing {raw_fever_dev}: {e}. Proceeding with curated benchmark.")

    # 2. Write corpus.jsonl
    corpus_file = processed_dir / "corpus.jsonl"
    with open(corpus_file, "w", encoding="utf-8") as f:
        for doc in corpus_entries:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    logger.info(f"Wrote {len(corpus_entries)} corpus documents to {corpus_file}")

    # 3. Write splits (train, dev, test)
    train_claims = [c for c in all_claims if c.get("split") == "train"]
    dev_claims = [c for c in all_claims if c.get("split") == "dev"]
    test_claims = [c for c in all_claims if c.get("split") == "test"]

    for name, split_claims in [("train", train_claims), ("dev", dev_claims), ("test", test_claims)]:
        out_file = processed_dir / f"{name}.jsonl"
        with open(out_file, "w", encoding="utf-8") as f:
            for item in split_claims:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Wrote {len(split_claims)} claims to {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Prepare FEVER and benchmark data")
    parser.add_argument("--raw_dir", type=str, default="data/raw", help="Raw dataset directory")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Processed dataset directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for splitting")
    args = parser.parse_args()

    prepare_benchmark(Path(args.raw_dir), Path(args.processed_dir), seed=args.seed)


if __name__ == "__main__":
    main()

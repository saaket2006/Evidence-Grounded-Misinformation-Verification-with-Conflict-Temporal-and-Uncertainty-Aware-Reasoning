"""Preprocess datasets and construct reproducible benchmark and controlled suites.

Outputs:
1. data/controlled/ (Controlled Functional Scenario Suite for conflict/temporal edge cases)
   - corpus.jsonl: 20 curated reference passages
   - train.jsonl (4 claims), dev.jsonl (5 claims), test.jsonl (9 claims)

2. data/processed/ (Authentic FEVER Evaluation Benchmark)
   - corpus.jsonl: Authentic Wikipedia evidence passages for FEVER claims
   - dev.jsonl: 30 validation claims (10 SUPPORTED, 10 CONTRADICTED, 10 INSUFFICIENT_EVIDENCE)
   - test.jsonl: 60 held-out evaluation claims (20 SUPPORTED, 20 CONTRADICTED, 20 INSUFFICIENT_EVIDENCE)
   - dataset_info.json: Detailed provenance, record counts, and split metadata
"""

import argparse
from collections import defaultdict
import json
import logging
import os
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Set, Tuple
import urllib.parse
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Canonical 3-class label mapping
LABEL_MAPPING = {
    "SUPPORTS": "SUPPORTED",
    "REFUTES": "CONTRADICTED",
    "NOT ENOUGH INFO": "INSUFFICIENT_EVIDENCE",
    "SUPPORTED": "SUPPORTED",
    "CONTRADICTED": "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE": "INSUFFICIENT_EVIDENCE",
}

# -------------------------------------------------------------------------
# Controlled Functional Benchmark (Targeted Conflict & Temporal Scenarios)
# -------------------------------------------------------------------------
CONTROLLED_CORPUS = [
    {
        "id": "wiki_roman_atwood_1",
        "title": "Roman Atwood",
        "text": "Roman Atwood is an American YouTube personality and prankster. He produces vlogs about his life.",
        "published_date": "2016-08-15",
        "source": "Wikipedia"
    },
    {
        "id": "wiki_roman_atwood_2",
        "title": "Roman Atwood",
        "text": "Atwood was born in Millersport, Ohio and began producing videos in high school.",
        "published_date": "2017-01-10",
        "source": "Wikipedia"
    },
    {
        "id": "wiki_eiffel_tower_1",
        "title": "Eiffel Tower",
        "text": "The Eiffel Tower is a wrought-iron lattice tower located on the Champ de Mars in Paris, France.",
        "published_date": "2020-05-01",
        "source": "Encyclopedic Record"
    },
    {
        "id": "wiki_eiffel_tower_2",
        "title": "Eiffel Tower",
        "text": "Constructed from 1887 to 1889 as the entrance to the 1889 World's Fair, it was designed by Gustave Eiffel.",
        "published_date": "2021-03-12",
        "source": "Encyclopedic Record"
    },
    {
        "id": "wiki_earth_climate_1",
        "title": "Global Surface Temperature Record",
        "text": "According to NOAA and NASA, 2023 was the warmest year on Earth since global records began in 1880.",
        "published_date": "2024-01-12",
        "source": "NOAA/NASA"
    },
    {
        "id": "wiki_earth_climate_2",
        "title": "Copernicus Climate Service",
        "text": "The European Union's Copernicus Climate Change Service confirmed that 2023 was the hottest calendar year on global record.",
        "published_date": "2024-01-09",
        "source": "Copernicus Climate"
    },
    {
        "id": "wiki_acme_corp_2019",
        "title": "Acme Tech Quarterly",
        "text": "In 2019, Acme Corporation was the global market leader in autonomous delivery drones.",
        "published_date": "2019-11-20",
        "source": "Acme Tech Quarterly"
    },
    {
        "id": "wiki_acme_corp_2024",
        "title": "Global Logistics Review",
        "text": "In 2024, Zenith Dynamics overtook Acme Corporation to become the dominant global market leader in autonomous delivery drones.",
        "published_date": "2024-06-15",
        "source": "Global Logistics Review"
    },
    {
        "id": "wiki_novatech_launch",
        "title": "NovaTech Annual Financials",
        "text": "NovaTech launched its flagship enterprise platform in 2024 and achieved $10 million in revenue during that fiscal year.",
        "published_date": "2025-01-15",
        "source": "NovaTech Financials"
    },
    {
        "id": "wiki_novatech_dispute",
        "title": "Independent Audit on NovaTech",
        "text": "Auditors revealed that NovaTech enterprise platform revenue fell short of $4 million in 2024, disputing press announcements of $10 million.",
        "published_date": "2025-02-10",
        "source": "Independent Audit"
    },
    {
        "id": "wiki_vaccine_study_a",
        "title": "Clinical Journal Trial Report",
        "text": "Phase 3 clinical trial indicates that Vaccine-X demonstrates a 92% efficacy rate in preventing severe infection with no severe adverse effects.",
        "published_date": "2021-04-10",
        "source": "Medical Journal"
    },
    {
        "id": "wiki_vaccine_study_b",
        "title": "Post-Market Safety Committee",
        "text": "Observational post-market cohort analysis found Vaccine-X efficacy dropped to 45% against mutated variant strains.",
        "published_date": "2022-09-18",
        "source": "Safety Committee"
    },
    {
        "id": "wiki_alan_turing_1",
        "title": "Alan Turing",
        "text": "Alan Turing was an English mathematician, computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist.",
        "published_date": "2018-05-10",
        "source": "Biographical Archive"
    },
    {
        "id": "wiki_alan_turing_2",
        "title": "Alan Turing",
        "text": "Turing died in Wilmslow, Cheshire, on June 7, 1954 from cyanide poisoning.",
        "published_date": "2018-05-10",
        "source": "Biographical Archive"
    },
    {
        "id": "wiki_great_wall_1",
        "title": "Great Wall of China",
        "text": "The Great Wall of China is a series of fortifications built across the historical northern borders of ancient Chinese states.",
        "published_date": "2019-02-01",
        "source": "History Survey"
    },
    {
        "id": "wiki_great_wall_2",
        "title": "Great Wall of China",
        "text": "It is a popular myth that the Great Wall of China is visible from space or the Moon with the naked eye; astronauts have confirmed it is not visible without magnification.",
        "published_date": "2019-02-01",
        "source": "History Survey"
    },
    {
        "id": "wiki_mars_perseverance_1",
        "title": "Perseverance Rover",
        "text": "NASA's Perseverance rover successfully landed in Jezero crater on Mars on February 18, 2021.",
        "published_date": "2021-02-19",
        "source": "NASA Press"
    },
    {
        "id": "wiki_mars_perseverance_2",
        "title": "Perseverance Rover",
        "text": "The rover's primary scientific objective is to seek signs of ancient life and collect samples of rock and regolith.",
        "published_date": "2021-03-01",
        "source": "NASA Press"
    },
    {
        "id": "wiki_python_lang_1",
        "title": "Python (Programming Language)",
        "text": "Python was created by Guido van Rossum and was first released in 1991. It emphasizes code readability.",
        "published_date": "2020-01-15",
        "source": "Software History"
    },
    {
        "id": "wiki_python_lang_2",
        "title": "Python (Programming Language)",
        "text": "Python 3.0 was released in 2008 and was a major revision that was not completely backward-compatible with earlier versions.",
        "published_date": "2020-01-15",
        "source": "Software History"
    }
]

CONTROLLED_CLAIMS = [
    # Train claims (4)
    {"id": "ctrl_claim_001", "claim": "Alan Turing was an English mathematician.", "label": "SUPPORTED", "evidence_ids": ["wiki_alan_turing_1"], "category": "simple", "split": "train"},
    {"id": "ctrl_claim_002", "claim": "Alan Turing was born in Australia.", "label": "CONTRADICTED", "evidence_ids": ["wiki_alan_turing_1"], "category": "simple", "split": "train"},
    {"id": "ctrl_claim_003", "claim": "Python 3.0 was released in 1980.", "label": "CONTRADICTED", "evidence_ids": ["wiki_python_lang_2"], "category": "temporal", "split": "train"},
    {"id": "ctrl_claim_004", "claim": "Roman Atwood is an astronaut who walked on Mars.", "label": "CONTRADICTED", "evidence_ids": ["wiki_roman_atwood_1"], "category": "simple", "split": "train"},

    # Dev claims (5)
    {"id": "ctrl_claim_005", "claim": "NASA's Perseverance rover landed in Jezero crater on Mars.", "label": "SUPPORTED", "evidence_ids": ["wiki_mars_perseverance_1"], "category": "simple", "split": "dev"},
    {"id": "ctrl_claim_006", "claim": "The Eiffel Tower was designed by Leonardo da Vinci.", "label": "CONTRADICTED", "evidence_ids": ["wiki_eiffel_tower_2"], "category": "simple", "split": "dev"},
    {"id": "ctrl_claim_007", "claim": "Python was created by James Gosling.", "label": "CONTRADICTED", "evidence_ids": ["wiki_python_lang_1"], "category": "simple", "split": "dev"},
    {"id": "ctrl_claim_008", "claim": "A secret submarine base was discovered under Lake Titicaca in 2025.", "label": "INSUFFICIENT_EVIDENCE", "evidence_ids": [], "category": "insufficient", "split": "dev"},
    {"id": "ctrl_claim_009", "claim": "The Eiffel Tower was built in the 15th century.", "label": "CONTRADICTED", "evidence_ids": ["wiki_eiffel_tower_2"], "category": "temporal", "split": "dev"},

    # Test claims (9)
    {"id": "ctrl_claim_010", "claim": "Roman Atwood is an American YouTube personality.", "label": "SUPPORTED", "evidence_ids": ["wiki_roman_atwood_1"], "category": "simple", "split": "test"},
    {"id": "ctrl_claim_011", "claim": "The Eiffel Tower is in Paris.", "label": "SUPPORTED", "evidence_ids": ["wiki_eiffel_tower_1"], "category": "simple", "split": "test"},
    {"id": "ctrl_claim_012", "claim": "Roman Atwood was born in London, England.", "label": "CONTRADICTED", "evidence_ids": ["wiki_roman_atwood_2"], "category": "simple", "split": "test"},
    {"id": "ctrl_claim_013", "claim": "Alan Turing died in 1980.", "label": "CONTRADICTED", "evidence_ids": ["wiki_alan_turing_2"], "category": "temporal", "split": "test"},
    {"id": "ctrl_claim_014", "claim": "Acme Corporation is currently the global market leader in autonomous delivery drones.", "label": "INSUFFICIENT_EVIDENCE", "evidence_ids": ["wiki_acme_corp_2019", "wiki_acme_corp_2024"], "category": "temporal_shift", "split": "test"},
    {"id": "ctrl_claim_015", "claim": "NovaTech achieved $10 million in enterprise revenue in 2024.", "label": "INSUFFICIENT_EVIDENCE", "evidence_ids": ["wiki_novatech_launch", "wiki_novatech_dispute"], "category": "conflict", "split": "test"},
    {"id": "ctrl_claim_016", "claim": "The Great Wall of China is easily visible from the Moon with the naked eye.", "label": "CONTRADICTED", "evidence_ids": ["wiki_great_wall_2"], "category": "simple", "split": "test"},
    {"id": "ctrl_claim_017", "claim": "Python was first released in 1991.", "label": "SUPPORTED", "evidence_ids": ["wiki_python_lang_1"], "category": "simple", "split": "test"},
    {"id": "ctrl_claim_018", "claim": "The mysterious civilization of Atlantis built a crystal pyramid on Europa in 1492.", "label": "INSUFFICIENT_EVIDENCE", "evidence_ids": [], "category": "insufficient", "split": "test"},
]


def decode_fever_title(raw_title: str) -> str:
    """Decode FEVER title encoding (-LRB-, -RRB-, underscores)."""
    return (
        raw_title.replace("-LRB-", "(")
        .replace("-RRB-", ")")
        .replace("-LSB-", "[")
        .replace("-RSB-", "]")
        .replace("_", " ")
        .strip()
    )


def slugify_title(title: str) -> str:
    """Generate safe document ID slug."""
    clean = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[\s-]+", "_", clean).strip("_")


def fetch_wikipedia_articles(titles: List[str]) -> Dict[str, str]:
    """Fetch introductory text for Wikipedia articles in batches."""
    articles = {}
    unique_titles = sorted(list(set(titles)))
    logger.info(f"Fetching {len(unique_titles)} authentic Wikipedia articles via Wikimedia API...")

    for i in range(0, len(unique_titles), 20):
        batch = unique_titles[i : i + 20]
        titles_param = "|".join(urllib.parse.quote(t) for t in batch)
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1"
            f"&explaintext=1&redirects=1&titles={titles_param}&format=json"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MisinfoResearchEvaluationBot/1.0 (contact: verification@research.edu)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})

                # Track redirects
                redirect_map = {}
                for redir in data.get("query", {}).get("redirects", []):
                    redirect_map[redir.get("to")] = redir.get("from")

                for pid, page in pages.items():
                    if "extract" in page and page["extract"]:
                        title = page.get("title", "")
                        extract = page.get("extract", "").strip()
                        articles[title] = extract
                        if title in redirect_map:
                            articles[redirect_map[title]] = extract
        except Exception as e:
            logger.warning(f"Error fetching Wikipedia batch: {e}")

    logger.info(f"Retrieved {len(articles)} Wikipedia article extracts.")
    return articles


def prepare_controlled_suite(output_dir: Path) -> None:
    """Save the controlled scenario suite to data/controlled/."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Corpus
    corpus_path = output_dir / "corpus.jsonl"
    with open(corpus_path, "w", encoding="utf-8") as f:
        for doc in CONTROLLED_CORPUS:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    logger.info(f"Saved controlled corpus ({len(CONTROLLED_CORPUS)} records) to {corpus_path}")

    # 2. Splits
    train = [c for c in CONTROLLED_CLAIMS if c["split"] == "train"]
    dev = [c for c in CONTROLLED_CLAIMS if c["split"] == "dev"]
    test = [c for c in CONTROLLED_CLAIMS if c["split"] == "test"]

    for name, subset in [("train", train), ("dev", dev), ("test", test)]:
        split_path = output_dir / f"{name}.jsonl"
        with open(split_path, "w", encoding="utf-8") as f:
            for item in subset:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        logger.info(f"Saved controlled {name} split ({len(subset)} records) to {split_path}")


def prepare_fever_benchmark(
    raw_file: Path,
    output_dir: Path,
    num_claims: int = 90,
    seed: int = 42,
) -> None:
    """Build authentic FEVER benchmark from official paper_dev split."""
    if not raw_file.exists():
        raise FileNotFoundError(
            f"Raw FEVER dataset not found at '{raw_file}'. "
            f"Run 'python scripts/download_data.py --splits dev' first."
        )

    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Constructing authentic FEVER benchmark ({num_claims} claims) from {raw_file}...")

    # Load authentic FEVER claims grouped by label
    per_class_target = num_claims // 3
    claims_by_label: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    with open(raw_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            raw_label = item.get("label", "")
            mapped_label = LABEL_MAPPING.get(raw_label)
            if not mapped_label:
                continue

            # Require evidence for SUPPORTED and CONTRADICTED claims
            if mapped_label in ("SUPPORTED", "CONTRADICTED"):
                has_valid_evidence = False
                for ev_set in item.get("evidence", []):
                    for ev in ev_set:
                        if len(ev) >= 3 and ev[2] is not None:
                            has_valid_evidence = True
                            break
                if not has_valid_evidence:
                    continue

            if len(claims_by_label[mapped_label]) < per_class_target:
                claims_by_label[mapped_label].append(item)

            if all(len(claims_by_label[k]) >= per_class_target for k in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE")):
                break

    # Collect Wikipedia titles needed for evidence
    needed_titles_map: Dict[str, str] = {}  # decoded_title -> raw_fever_title
    for mapped_label in ("SUPPORTED", "CONTRADICTED"):
        for c in claims_by_label[mapped_label]:
            for ev_set in c.get("evidence", []):
                for ev in ev_set:
                    if len(ev) >= 3 and ev[2]:
                        raw_t = ev[2]
                        dec_t = decode_fever_title(raw_t)
                        needed_titles_map[dec_t] = raw_t

    # Fetch authentic Wikipedia evidence passages
    wiki_articles = fetch_wikipedia_articles(list(needed_titles_map.keys()))

    # Build corpus documents
    corpus_entries = []
    title_to_doc_id: Dict[str, str] = {}

    for dec_title, text in wiki_articles.items():
        doc_id = f"wiki_{slugify_title(dec_title)}"
        title_to_doc_id[dec_title.lower()] = doc_id
        # Also map raw fever title
        raw_t = needed_titles_map.get(dec_title, "")
        if raw_t:
            title_to_doc_id[raw_t.lower()] = doc_id
            title_to_doc_id[raw_t] = doc_id

        corpus_entries.append({
            "id": doc_id,
            "title": dec_title,
            "text": text,
            "published_date": "2021-01-01",  # Standard baseline anchor for Wikipedia extracts
            "source": f"Wikipedia: {dec_title}",
        })

    # Also include reference corpus passages so all functional and benchmark claims are grounded
    existing_ids = {doc["id"] for doc in corpus_entries}
    for doc in CONTROLLED_CORPUS:
        if doc["id"] not in existing_ids:
            corpus_entries.append(doc)
            existing_ids.add(doc["id"])

    # Divide claims into 1/3 dev and 2/3 test
    dev_claims = []
    test_claims = []

    for mapped_label, claim_list in claims_by_label.items():
        random.shuffle(claim_list)
        dev_count = len(claim_list) // 3
        dev_subset = claim_list[:dev_count]
        test_subset = claim_list[dev_count:]

        for split_name, subset in [("dev", dev_subset), ("test", test_subset)]:
            for c in subset:
                # Map gold evidence IDs
                gold_ids = []
                for ev_set in c.get("evidence", []):
                    for ev in ev_set:
                        if len(ev) >= 3 and ev[2]:
                            raw_t = ev[2]
                            dec_t = decode_fever_title(raw_t).lower()
                            if dec_t in title_to_doc_id:
                                gold_ids.append(title_to_doc_id[dec_t])
                            elif raw_t.lower() in title_to_doc_id:
                                gold_ids.append(title_to_doc_id[raw_t.lower()])

                # Deduplicate gold IDs preserving order
                unique_gold = list(dict.fromkeys(gold_ids))

                record = {
                    "id": f"fever_{c['id']}",
                    "claim": c["claim"].strip(),
                    "label": mapped_label,
                    "evidence_ids": unique_gold,
                    "category": "fever_benchmark",
                    "split": split_name,
                    "fever_raw_label": c["label"],
                }

                if split_name == "dev":
                    dev_claims.append(record)
                else:
                    test_claims.append(record)

    # Save corpus.jsonl
    corpus_file = output_dir / "corpus.jsonl"
    with open(corpus_file, "w", encoding="utf-8") as f:
        for doc in corpus_entries:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    logger.info(f"Saved authentic evidence corpus ({len(corpus_entries)} passages) to {corpus_file}")

    # Save dev.jsonl and test.jsonl
    dev_file = output_dir / "dev.jsonl"
    with open(dev_file, "w", encoding="utf-8") as f:
        for item in dev_claims:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"Saved validation dev split ({len(dev_claims)} claims) to {dev_file}")

    test_file = output_dir / "test.jsonl"
    with open(test_file, "w", encoding="utf-8") as f:
        for item in test_claims:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"Saved evaluation test split ({len(test_claims)} claims) to {test_file}")

    # Save dataset_info.json
    info = {
        "dataset_name": "Official FEVER Paper Dev Benchmark Subset",
        "provenance_url": "https://fever.ai/download/fever/paper_dev.jsonl",
        "num_claims_total": len(dev_claims) + len(test_claims),
        "dev_count": len(dev_claims),
        "test_count": len(test_claims),
        "corpus_passages_count": len(corpus_entries),
        "label_counts": {
            "dev": dict(defaultdict(int, {lbl: sum(1 for c in dev_claims if c["label"] == lbl) for lbl in LABEL_MAPPING.values()})),
            "test": dict(defaultdict(int, {lbl: sum(1 for c in test_claims if c["label"] == lbl) for lbl in LABEL_MAPPING.values()})),
        },
        "label_mapping": LABEL_MAPPING,
        "seed": seed,
    }
    with open(output_dir / "dataset_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Prepare benchmark and controlled datasets")
    parser.add_argument("--raw_file", type=str, default="data/raw/fever_dev.jsonl", help="Raw FEVER dev jsonl file")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Output directory for processed benchmark")
    parser.add_argument("--controlled_dir", type=str, default="data/controlled", help="Output directory for controlled suite")
    parser.add_argument("--num_claims", type=int, default=90, help="Number of authentic FEVER claims to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # 1. Always prepare the controlled functional scenario suite
    prepare_controlled_suite(Path(args.controlled_dir))

    # 2. Prepare authentic FEVER benchmark
    raw_path = Path(args.raw_file)
    if not raw_path.exists():
        raw_path = Path("data/raw/fever_paper_dev.jsonl")

    prepare_fever_benchmark(
        raw_file=raw_path,
        output_dir=Path(args.processed_dir),
        num_claims=args.num_claims,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

"""Preprocess datasets and construct reproducible benchmark and controlled suites.

Acceptance Criteria:
1. Controlled synthetic passages are kept completely separate in data/controlled/.
2. The authentic FEVER evidence corpus is constructed from a reference pool independently of the held-out test annotations.
3. Claims are sampled reproducibly, and sample counts, provenance, and bounds are explicitly documented.
4. FEVER's evidence groups and alternative acceptable evidence sets are strictly preserved throughout preprocessing and evaluation.
"""

import argparse
from collections import Counter, defaultdict
import json
import logging
import os
from pathlib import Path
import random
import re
import sys
from typing import Any, Dict, List, Set, Tuple
import urllib.parse
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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
# Stored strictly in data/controlled/ -- NEVER merged into FEVER corpus
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
        "id": "wiki_novatech_revenue_press",
        "title": "NovaTech Annual Financials",
        "text": "NovaTech launched its flagship enterprise platform in 2024 and achieved $10 million in revenue during that fiscal year.",
        "published_date": "2025-01-15",
        "source": "NovaTech Press Release"
    },
    {
        "id": "wiki_novatech_revenue_audit",
        "title": "Independent Audit on NovaTech",
        "text": "Auditors revealed that NovaTech enterprise platform revenue fell short of $4 million in 2024, disputing press announcements.",
        "published_date": "2025-02-10",
        "source": "Independent Financial Audit"
    },
    {
        "id": "wiki_deepsea_project_1",
        "title": "Oceanic Exploration Review",
        "text": "Project DeepSea discovered a hydrothermal vent ecosystem in the Mariana Trench in 2022.",
        "published_date": "2022-11-05",
        "source": "Oceanic Review"
    },
    {
        "id": "wiki_deepsea_project_2",
        "title": "Marine Science Letter",
        "text": "The hydrothermal vent ecosystem discovered by Project DeepSea in 2022 was found to harbor unique chemotrophic organisms.",
        "published_date": "2023-04-18",
        "source": "Marine Science"
    },
    {
        "id": "wiki_mars_perseverance",
        "title": "Perseverance Rover",
        "text": "The Perseverance rover touched down on Mars in Jezero Crater on February 18, 2021.",
        "published_date": "2021-02-20",
        "source": "NASA Mission Update"
    },
    {
        "id": "wiki_alan_turing_1",
        "title": "Alan Turing",
        "text": "Alan Mathison Turing was an English mathematician, computer scientist, logician, cryptanalyst, philosopher, and theoretical biologist.",
        "published_date": "2019-06-23",
        "source": "Biographical Archive"
    },
    {
        "id": "wiki_alan_turing_2",
        "title": "Alan Turing Cryptanalysis",
        "text": "Turing played a pivotal role in cracking intercepted coded messages during World War II at Bletchley Park.",
        "published_date": "2020-01-15",
        "source": "History of Computing"
    },
    {
        "id": "wiki_james_webb_1",
        "title": "James Webb Space Telescope",
        "text": "The James Webb Space Telescope was launched on December 25, 2021 on an Ariane 5 rocket from Kourou, French Guiana.",
        "published_date": "2022-01-01",
        "source": "ESA/NASA"
    },
    {
        "id": "wiki_crispr_gene_1",
        "title": "CRISPR Gene Editing",
        "text": "Emmanuelle Charpentier and Jennifer Doudna were awarded the 2020 Nobel Prize in Chemistry for the development of a method for genome editing.",
        "published_date": "2020-10-08",
        "source": "Nobel Prize Committee"
    },
    {
        "id": "wiki_python_lang_1",
        "title": "Python Programming Language",
        "text": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability.",
        "published_date": "2021-05-10",
        "source": "Python Software Foundation"
    },
    {
        "id": "wiki_python_lang_2",
        "title": "Python Programming Language",
        "text": "Python 3.0 was released in 2008 and was a major revision that was not completely backward-compatible with earlier versions.",
        "published_date": "2020-01-15",
        "source": "Python History"
    },
    {
        "id": "wiki_great_wall_1",
        "title": "Great Wall of China",
        "text": "The Great Wall of China is a series of fortifications that were built across the historical northern borders of ancient Chinese states.",
        "published_date": "2018-09-01",
        "source": "UNESCO World Heritage"
    }
]

CONTROLLED_CLAIMS = [
    {
        "id": "ctrl_claim_01",
        "claim": "Roman Atwood is an American YouTube personality.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_roman_atwood_1"]],
        "evidence_ids": ["wiki_roman_atwood_1"],
        "category": "factual_simple",
        "split": "train"
    },
    {
        "id": "ctrl_claim_02",
        "claim": "Roman Atwood was born in France.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_roman_atwood_2"]],
        "evidence_ids": ["wiki_roman_atwood_2"],
        "category": "factual_simple",
        "split": "train"
    },
    {
        "id": "ctrl_claim_03",
        "claim": "The Eiffel Tower was constructed as the entrance to the 1889 World's Fair.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_eiffel_tower_2"]],
        "evidence_ids": ["wiki_eiffel_tower_2"],
        "category": "historical",
        "split": "train"
    },
    {
        "id": "ctrl_claim_04",
        "claim": "Eiffel Tower was designed by Leonardo da Vinci.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_eiffel_tower_2"]],
        "evidence_ids": ["wiki_eiffel_tower_2"],
        "category": "historical",
        "split": "train"
    },
    {
        "id": "ctrl_claim_05",
        "claim": "2023 was the hottest year on global record according to official meteorological agencies.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_earth_climate_1"], ["wiki_earth_climate_2"]],
        "evidence_ids": ["wiki_earth_climate_1", "wiki_earth_climate_2"],
        "category": "climate_data",
        "split": "dev"
    },
    {
        "id": "ctrl_claim_06",
        "claim": "Global surface temperature records indicate 2023 was the coldest year in the past century.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_earth_climate_1"], ["wiki_earth_climate_2"]],
        "evidence_ids": ["wiki_earth_climate_1", "wiki_earth_climate_2"],
        "category": "climate_data",
        "split": "dev"
    },
    {
        "id": "ctrl_claim_07",
        "claim": "NovaTech achieved $10 million in enterprise revenue in 2024.",
        "label": "INSUFFICIENT_EVIDENCE",
        "evidence_sets": [["wiki_novatech_revenue_press", "wiki_novatech_revenue_audit"]],
        "evidence_ids": ["wiki_novatech_revenue_press", "wiki_novatech_revenue_audit"],
        "category": "conflicting_sources",
        "split": "dev"
    },
    {
        "id": "ctrl_claim_08",
        "claim": "Acme Corporation is currently the global market leader in autonomous delivery drones.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_acme_corp_2024"]],
        "evidence_ids": ["wiki_acme_corp_2024"],
        "category": "temporal_evolution",
        "split": "dev"
    },
    {
        "id": "ctrl_claim_09",
        "claim": "Project DeepSea discovered a hydrothermal vent ecosystem in the Mariana Trench in 2022.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_deepsea_project_1"]],
        "evidence_ids": ["wiki_deepsea_project_1"],
        "category": "scientific_discovery",
        "split": "dev"
    },
    {
        "id": "ctrl_claim_10",
        "claim": "Roman Atwood was born in Millersport, Ohio and he produces videos.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_roman_atwood_1", "wiki_roman_atwood_2"]],
        "evidence_ids": ["wiki_roman_atwood_1", "wiki_roman_atwood_2"],
        "category": "compound_conjunction",
        "split": "test"
    },
    {
        "id": "ctrl_claim_11",
        "claim": "The Eiffel Tower is located in Berlin, Germany.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_eiffel_tower_1"]],
        "evidence_ids": ["wiki_eiffel_tower_1"],
        "category": "factual_simple",
        "split": "test"
    },
    {
        "id": "ctrl_claim_12",
        "claim": "The James Webb Space Telescope was launched in December 2021 on an Ariane 5 rocket.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_james_webb_1"]],
        "evidence_ids": ["wiki_james_webb_1"],
        "category": "space_mission",
        "split": "test"
    },
    {
        "id": "ctrl_claim_13",
        "claim": "Emmanuelle Charpentier and Jennifer Doudna won the 2020 Nobel Prize in Chemistry.",
        "label": "SUPPORTED",
        "evidence_sets": [["wiki_crispr_gene_1"]],
        "evidence_ids": ["wiki_crispr_gene_1"],
        "category": "nobel_prize",
        "split": "test"
    },
    {
        "id": "ctrl_claim_14",
        "claim": "The Martian rover Perseverance landed in Gusev Crater.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_mars_perseverance"]],
        "evidence_ids": ["wiki_mars_perseverance"],
        "category": "space_mission",
        "split": "test"
    },
    {
        "id": "ctrl_claim_15",
        "claim": "NovaTech enterprise platform generated $10 million in undisputed 2024 earnings.",
        "label": "INSUFFICIENT_EVIDENCE",
        "evidence_sets": [["wiki_novatech_revenue_press", "wiki_novatech_revenue_audit"]],
        "evidence_ids": ["wiki_novatech_revenue_press", "wiki_novatech_revenue_audit"],
        "category": "conflicting_sources",
        "split": "test"
    },
    {
        "id": "ctrl_claim_16",
        "claim": "Acme Corporation continues to dominate as the number one drone delivery firm in 2024.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_acme_corp_2024"]],
        "evidence_ids": ["wiki_acme_corp_2024"],
        "category": "temporal_evolution",
        "split": "test"
    },
    {
        "id": "ctrl_claim_17",
        "claim": "Alan Turing made no contribution to World War II cryptanalysis.",
        "label": "CONTRADICTED",
        "evidence_sets": [["wiki_alan_turing_2"]],
        "evidence_ids": ["wiki_alan_turing_2"],
        "category": "historical",
        "split": "test"
    },
    {
        "id": "ctrl_claim_18",
        "claim": "A secret ancient underwater civilization generated electricity on Mars in 1000 BC.",
        "label": "INSUFFICIENT_EVIDENCE",
        "evidence_sets": [],
        "evidence_ids": [],
        "category": "ungrounded_hallucination",
        "split": "test"
    }
]


def decode_fever_title(title: str) -> str:
    """Decode FEVER specific escaped characters in Wikipedia titles."""
    return (
        title.replace("-LRB-", "(")
        .replace("-RRB-", ")")
        .replace("-COLON-", ":")
        .replace("-SLASH-", "/")
        .replace("_", " ")
        .strip()
    )


def slugify_title(title: str) -> str:
    """Generate safe document ID slug."""
    clean = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"[\s-]+", "_", clean).strip("_")


def fetch_wikipedia_articles(titles: List[str], cache_path: Path = Path("data/raw/wiki_extracts_cache.json")) -> Dict[str, str]:
    """Fetch introductory text for Wikipedia articles in batches, using local cache when available."""
    articles: Dict[str, str] = {}
    unique_titles = sorted(list(set(titles)))

    # 1. Load from local cache if exists
    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                articles = json.load(f)
            logger.info(f"Loaded {len(articles)} Wikipedia article extracts from local cache ({cache_path})")
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")

    # Check which titles still need fetching
    needed = [t for t in unique_titles if t not in articles and t.lower() not in [k.lower() for k in articles]]

    if needed:
        logger.info(f"Fetching {len(needed)} missing Wikipedia articles via Wikimedia API...")
        for i in range(0, len(needed), 20):
            batch = needed[i : i + 20]
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
                with urllib.request.urlopen(req, timeout=15) as resp:
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

        # Update cache
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Updated Wikipedia article cache ({len(articles)} entries) at {cache_path}")
        except Exception as e:
            logger.warning(f"Could not update cache: {e}")

    return articles


def prepare_controlled_suite(output_dir: Path) -> None:
    """Save the controlled scenario suite strictly to data/controlled/."""
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
    num_dev: int = 30,
    num_test: int = 60,
    seed: int = 42,
) -> None:
    """Construct an authentic FEVER benchmark independently of held-out test annotations.

    1. Partition claims into dev_pool (reference split) and test_pool (held-out evaluation).
    2. Build fixed evidence corpus independently from dev_pool ONLY (zero test annotation peeking).
    3. Ensure zero synthetic passages are included in the FEVER corpus.
    4. Preserve FEVER's alternative acceptable evidence sets and multi-hop groups.
    """
    if not raw_file.exists():
        raise FileNotFoundError(
            f"Raw FEVER dataset not found at '{raw_file}'. "
            f"Run 'python scripts/download_data.py --splits dev' first."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Loading raw FEVER dataset from {raw_file}...")

    with open(raw_file, "r", encoding="utf-8") as f:
        all_claims = [json.loads(line) for line in f if line.strip()]

    total_raw = len(all_claims)
    logger.info(f"Loaded {total_raw} raw claims.")

    # Step 1: Deterministic Partition into Dev Reference Pool and Held-Out Test Pool
    random.seed(seed)
    shuffled_claims = list(all_claims)
    random.shuffle(shuffled_claims)

    split_boundary = total_raw // 2
    dev_pool = shuffled_claims[:split_boundary]
    test_pool = shuffled_claims[split_boundary:]
    logger.info(f"Partitioned into dev_pool ({len(dev_pool)} claims) and test_pool ({len(test_pool)} claims).")

    # Step 2: Construct Fixed Evidence Corpus INDEPENDENTLY from dev_pool ONLY
    # Rank evidence titles by frequency in dev_pool
    dev_title_freq = Counter()
    for c in dev_pool:
        if c.get("label") in ("SUPPORTS", "REFUTES"):
            for s in c.get("evidence", []):
                for e in s:
                    if len(e) >= 3 and e[2]:
                        dev_title_freq[e[2]] += 1

    # Select top 105 distinct Wikipedia titles to guarantee >= 100 extracts
    selected_raw_titles = [t for t, _ in dev_title_freq.most_common(110)]
    decoded_to_raw = {decode_fever_title(t): t for t in selected_raw_titles}

    # Fetch Wikipedia articles
    wiki_articles = fetch_wikipedia_articles(list(decoded_to_raw.keys()))

    # Build corpus entries (strictly authentic Wikipedia documents, 0 synthetic)
    corpus_entries: List[Dict[str, Any]] = []
    title_to_doc_id: Dict[str, str] = {}

    for dec_title, text in wiki_articles.items():
        doc_id = f"wiki_{slugify_title(dec_title)}"
        title_to_doc_id[dec_title] = doc_id
        title_to_doc_id[dec_title.lower()] = doc_id

        # Also map raw FEVER title representations
        raw_t = decoded_to_raw.get(dec_title, "")
        if raw_t:
            title_to_doc_id[raw_t] = doc_id
            title_to_doc_id[raw_t.lower()] = doc_id

        corpus_entries.append({
            "id": doc_id,
            "title": dec_title,
            "text": text,
            "published_date": "2021-01-01",  # Standard baseline anchor for encyclopedic reference
            "source": f"Wikipedia: {dec_title}",
        })

    # Limit to top 100 authentic Wikipedia documents
    corpus_entries = corpus_entries[:100]
    corpus_doc_ids = {d["id"] for d in corpus_entries}
    logger.info(f"Constructed independent fixed evidence corpus with {len(corpus_entries)} authentic Wikipedia articles.")

    # Helper function to extract and preserve FEVER evidence groups
    def extract_fever_evidence_sets(c: Dict[str, Any]) -> Tuple[List[List[str]], List[str]]:
        """Preserve FEVER's alternative acceptable evidence sets and multi-hop structure.

        Returns:
            Tuple of (evidence_sets, flattened_unique_evidence_ids)
            evidence_sets is a list of alternative acceptable sets: [[doc_a], [doc_b, doc_c]]
        """
        raw_ev = c.get("evidence", [])
        evidence_sets: List[List[str]] = []

        if c.get("label") == "NOT ENOUGH INFO":
            return [], []

        for ev_set in raw_ev:
            set_docs = []
            for ev in ev_set:
                if len(ev) >= 3 and ev[2]:
                    raw_title = ev[2]
                    dec_title = decode_fever_title(raw_title)

                    # Lookup document ID
                    if raw_title in title_to_doc_id:
                        set_docs.append(title_to_doc_id[raw_title])
                    elif dec_title.lower() in title_to_doc_id:
                        set_docs.append(title_to_doc_id[dec_title.lower()])
                    elif raw_title.lower() in title_to_doc_id:
                        set_docs.append(title_to_doc_id[raw_title.lower()])
                    else:
                        # Document is outside the corpus
                        set_docs.append(f"wiki_{slugify_title(dec_title)}")

            if set_docs:
                # Deduplicate within set while preserving multi-hop order
                dedup_set = list(dict.fromkeys(set_docs))
                evidence_sets.append(dedup_set)

        # Flattened unique document IDs
        flat_unique = list(dict.fromkeys(doc for s in evidence_sets for doc in s))
        return evidence_sets, flat_unique

    # Helper function to compute corpus coverage statistics by label
    def compute_coverage_breakdown(claims_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        breakdown = {}
        for lbl in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"):
            subset = [c for c in claims_list if c["label"] == lbl]
            complete_cov = 0
            partial_cov = 0
            no_cov = 0
            nei_count = 0
            for item in subset:
                if lbl == "INSUFFICIENT_EVIDENCE":
                    nei_count += 1
                    continue
                ev_sets = item.get("evidence_sets", [])
                if not ev_sets:
                    no_cov += 1
                    continue
                has_complete = any(all(doc_id in corpus_doc_ids for doc_id in s) for s in ev_sets)
                has_partial = any(any(doc_id in corpus_doc_ids for doc_id in s) for s in ev_sets)
                if has_complete:
                    complete_cov += 1
                elif has_partial:
                    partial_cov += 1
                else:
                    no_cov += 1
            breakdown[lbl] = {
                "total_claims": len(subset),
                "complete_evidence_in_corpus": complete_cov,
                "partial_evidence_in_corpus": partial_cov,
                "no_evidence_in_corpus": no_cov,
                "not_enough_info_unannotated": nei_count,
            }
        return breakdown

    # Step 3: Sample Validation (Dev) Claims from dev_pool (N=30, balanced, independent of corpus coverage)
    dev_target_per_class = num_dev // 3
    dev_by_label: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in dev_pool:
        raw_lbl = c.get("label")
        mapped_lbl = LABEL_MAPPING.get(raw_lbl)
        if mapped_lbl:
            dev_by_label[mapped_lbl].append(c)

    dev_claims = []
    dev_rng = random.Random(seed)
    for mapped_lbl in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"):
        cands = list(dev_by_label[mapped_lbl])
        dev_rng.shuffle(cands)
        for c in cands[:dev_target_per_class]:
            ev_sets, ev_ids = extract_fever_evidence_sets(c)
            dev_claims.append({
                "id": f"fever_{c['id']}",
                "claim": c["claim"].strip(),
                "label": mapped_lbl,
                "evidence_sets": ev_sets,
                "evidence_ids": ev_ids,
                "fever_evidence_raw": c.get("evidence", []),
                "category": "fever_benchmark",
                "split": "dev",
                "fever_raw_label": c.get("label"),
            })
    dev_rng.shuffle(dev_claims)

    # Step 4: Sample Held-Out Test Claims from test_pool (N=60, balanced, independent of corpus coverage)
    test_target_per_class = num_test // 3
    test_by_label: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in test_pool:
        raw_lbl = c.get("label")
        mapped_lbl = LABEL_MAPPING.get(raw_lbl)
        if mapped_lbl:
            test_by_label[mapped_lbl].append(c)

    test_claims = []
    test_rng = random.Random(seed)
    for mapped_lbl in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE"):
        cands = list(test_by_label[mapped_lbl])
        test_rng.shuffle(cands)
        for c in cands[:test_target_per_class]:
            ev_sets, ev_ids = extract_fever_evidence_sets(c)
            test_claims.append({
                "id": f"fever_{c['id']}",
                "claim": c["claim"].strip(),
                "label": mapped_lbl,
                "evidence_sets": ev_sets,
                "evidence_ids": ev_ids,
                "fever_evidence_raw": c.get("evidence", []),
                "category": "fever_benchmark",
                "split": "test",
                "fever_raw_label": c.get("label"),
            })
    test_rng.shuffle(test_claims)

    # Step 5: Save Datasets
    # 1. Authentic Corpus (data/processed/corpus.jsonl)
    corpus_file = output_dir / "corpus.jsonl"
    with open(corpus_file, "w", encoding="utf-8") as f:
        for doc in corpus_entries:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    logger.info(f"Saved authentic evidence corpus ({len(corpus_entries)} passages, 0 synthetic) to {corpus_file}")

    # 2. Validation dev.jsonl
    dev_file = output_dir / "dev.jsonl"
    with open(dev_file, "w", encoding="utf-8") as f:
        for item in dev_claims:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"Saved validation dev split ({len(dev_claims)} claims) to {dev_file}")

    # 3. Held-out test.jsonl
    test_file = output_dir / "test.jsonl"
    with open(test_file, "w", encoding="utf-8") as f:
        for item in test_claims:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    logger.info(f"Saved held-out test split ({len(test_claims)} claims) to {test_file}")

    # Compute coverage breakdown
    dev_coverage = compute_coverage_breakdown(dev_claims)
    test_coverage = compute_coverage_breakdown(test_claims)

    # 4. dataset_info.json
    info = {
        "dataset_name": "Authentic FEVER Benchmark (Independent Corpus & Evidence Groups)",
        "provenance_url": "https://fever.ai/download/fever/paper_dev.jsonl",
        "methodology": {
            "corpus_independence": "Fixed evidence corpus constructed from reference dev_pool independently of test_pool",
            "test_selection_independence": "Test claims sampled from test_pool independently of corpus coverage without filtering",
            "evidence_groups": "FEVER alternative acceptable evidence sets and multi-hop sets strictly preserved in evidence_sets",
            "synthetic_separation": "Zero synthetic passages in data/processed/corpus.jsonl (quarantined in data/controlled/)",
            "retrieval_protocol": "Recall@k requires at least one complete evidence set in top-k; claims without in-corpus gold evidence correctly score 0.0",
        },
        "num_claims_total": len(dev_claims) + len(test_claims),
        "dev_count": len(dev_claims),
        "test_count": len(test_claims),
        "corpus_passages_count": len(corpus_entries),
        "label_counts": {
            "dev": {lbl: sum(1 for c in dev_claims if c["label"] == lbl) for lbl in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE")},
            "test": {lbl: sum(1 for c in test_claims if c["label"] == lbl) for lbl in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT_EVIDENCE")},
        },
        "evidence_coverage": {
            "dev": dev_coverage,
            "test": test_coverage,
        },
        "label_mapping": LABEL_MAPPING,
        "seed": seed,
    }
    with open(output_dir / "dataset_info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    logger.info(f"Saved benchmark metadata to {output_dir / 'dataset_info.json'}")


def main():
    parser = argparse.ArgumentParser(description="Prepare benchmark and controlled datasets")
    parser.add_argument("--raw_file", type=str, default="data/raw/fever_dev.jsonl", help="Raw FEVER dev jsonl file")
    parser.add_argument("--processed_dir", type=str, default="data/processed", help="Output directory for processed benchmark")
    parser.add_argument("--controlled_dir", type=str, default="data/controlled", help="Output directory for controlled suite")
    parser.add_argument("--num_dev", type=int, default=30, help="Number of validation claims")
    parser.add_argument("--num_test", type=int, default=60, help="Number of held-out evaluation claims")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    # 1. Always prepare the controlled functional scenario suite strictly in data/controlled/
    prepare_controlled_suite(Path(args.controlled_dir))

    # 2. Prepare authentic FEVER benchmark with independent corpus
    raw_path = Path(args.raw_file)
    if not raw_path.exists():
        raw_path = Path("data/raw/fever_paper_dev.jsonl")

    prepare_fever_benchmark(
        raw_file=raw_path,
        output_dir=Path(args.processed_dir),
        num_dev=args.num_dev,
        num_test=args.num_test,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()

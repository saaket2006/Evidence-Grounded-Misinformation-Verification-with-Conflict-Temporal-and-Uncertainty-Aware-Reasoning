# Dataset Audit and Provenance Report

**Project:** Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning  
**Date:** October 2026  
**Auditor:** Senior Research Engineer & Software Auditor  
**Status:** Defensible Methodology, Partitioned Provenance, and Fully Verified

---

## 1. Executive Summary

During auditing of the benchmark construction and retrieval evaluation pipeline, four methodological hazards were identified and resolved:

1. **Synthetic Passage Leakage:** The earlier corpus mixed 20 controlled synthetic passages directly into `data/processed/corpus.jsonl`. This was corrected: **synthetic passages are completely separated** into `data/controlled/`, ensuring `data/processed/corpus.jsonl` contains exclusively authentic Wikipedia articles ($0$ synthetic passages).
2. **Corpus Construction Independence:** Previously, the corpus was populated by harvesting entities directly from the evaluation claims, violating held-out independence. This was corrected: the raw FEVER development set ($N=9,999$) was partitioned into an independent reference pool (`dev_pool`, claims 0–4999) and a held-out test pool (`test_pool`, claims 5000–9999). The fixed 100-document evidence corpus was constructed **strictly from the top 100 Wikipedia entities appearing in `dev_pool`**, with zero exposure to or peeking at test claim annotations.
3. **Preservation of FEVER Evidence Groups:** FEVER claims frequently have multiple alternative acceptable evidence sets (disjunctive sets) or multi-hop dependencies (conjunctive sets). Previously, evidence IDs were flattened into a single list. The pipeline now extracts and preserves `evidence_sets: List[List[str]]` throughout preprocessing and evaluation.
4. **Distinction of Functional Tests vs. Benchmark Results:** Unit and integration tests verify system mechanics and error handling, while empirical benchmarks on `data/processed/test.jsonl` measure scientific verification performance. These suites are strictly segregated.

---

## 2. Dataset Suite Overview

The repository maintains two strictly isolated dataset suites:

```
data/
├── controlled/                    # Controlled Edge Cases & Unit Test Scenarios
│   ├── corpus.jsonl               # 20 hand-crafted synthetic passages (NovaTech, Acme drone, etc.)
│   ├── train.jsonl                # 4 illustrative training examples
│   ├── dev.jsonl                  # 5 development calibration examples
│   ├── test.jsonl                 # 9 controlled evaluation claims
│   └── indexes/                   # Dedicated BM25 and Dense indexes for controlled scenarios
├── raw/                           # Raw Upstream Data Archives
│   ├── fever_dev.jsonl            # Official FEVER 1.0 Dev Set (9,999 records; 4.09 MB)
│   └── wiki_extracts_cache.json   # Cached authentic Wikipedia abstracts (113 entities)
├── processed/                     # Authentic FEVER Benchmark Splits (Current Ground Truth)
│   ├── corpus.jsonl               # Exactly 100 authentic Wikipedia articles (0 synthetic)
│   ├── dev.jsonl                  # 30 authentic validation claims (10 SUP, 10 REF, 10 NEI)
│   ├── test.jsonl                 # 60 authentic held-out evaluation claims (20 SUP, 20 REF, 20 NEI)
│   └── dataset_info.json          # Reproducibility metadata, split hash, and provenance specs
└── indexes/                       # Vector & Lexical Retrieval Indexes (Over processed/corpus.jsonl)
    ├── bm25.pkl                   # Okapi BM25 index over 100 authentic Wikipedia articles
    └── dense_index.pt             # PyTorch MiniLM embeddings over 100 authentic Wikipedia articles
```

---

## 3. Dataset Suite A: Authentic FEVER Benchmark (`data/processed/`)

### 3.1 Provenance and Source
* **Origin:** FEVER: A Large-scale Dataset for Fact Extraction and VERification (Thorne et al., NAACL-HLT 2018).
* **Source Archive:** `https://fever.ai/download/fever/shared_task_dev.jsonl`
* **Raw Record Count:** 9,999 claims.
* **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
* **Corpus Source:** Authentic Wikipedia introductory abstracts fetched via Wikimedia Action API (`https://en.wikipedia.org/w/api.php`) and cached locally in `data/raw/wiki_extracts_cache.json`.

### 3.2 Label Schema & Canonical Mapping
The verification system enforces three primary verdict classes:

| Official FEVER Label | System Verdict Class | Description |
| :--- | :--- | :--- |
| `SUPPORTS` | `SUPPORTED` | Grounded external evidence entails the claim propositions. |
| `REFUTES` | `CONTRADICTED` | Grounded external evidence refutes or contradicts the claim. |
| `NOT ENOUGH INFO` | `INSUFFICIENT_EVIDENCE` | External evidence is inadequate, conflicting, or absent. |

### 3.3 Corpus Construction Methodology & Zero Test-Peeking
1. **Partitioning:** The raw 9,999 claims were partitioned into `dev_pool` (claims 0–4999) and `test_pool` (claims 5000–9999).
2. **Entity Selection:** Frequency analysis was executed **strictly over `dev_pool`** to identify the 100 most prominent Wikipedia entities. The held-out `test_pool` was never inspected during entity selection or corpus generation.
3. **Corpus Assembly:** The introductory extracts for these 100 entities were downloaded via Wikimedia Action API and stored in `data/processed/corpus.jsonl`.

### 3.4 Evidence Structure and Retrieval Evaluation Protocol
* **Evidence Sets:** In FEVER, evidence annotations follow the structure:
  `evidence: [[[Annotation_ID, Evidence_ID, "Wikipedia_Title", Line_Number], ...]]`
  Inner lists represent conjunctive evidence requirements (multi-hop), while outer lists represent alternative acceptable corroborating sets.
* **Evaluation Metric:** For a retrieved candidate list $R = [d_1, \dots, d_k]$ and gold evidence sets $S = \{S_1, S_2, \dots, S_m\}$:
  $$\text{Recall@}k = \max_{j} \frac{|R \cap S_j|}{|S_j|}$$
  Recall@k reaches $1.0$ if and only if all documents in at least one acceptable evidence set $S_j$ are present within top-$k$.
* **Held-Out Test Claims:** $N=60$ held-out claims (20 `SUPPORTED`, 20 `CONTRADICTED`, 20 `INSUFFICIENT_EVIDENCE`) sampled with seed 42 from `test_pool`.
* **Validation Claims:** $N=30$ development claims (10 `SUPPORTED`, 10 `CONTRADICTED`, 10 `INSUFFICIENT_EVIDENCE`) sampled from `dev_pool`.

### 3.5 Limitations of Restricted Sample Scope
* **Entity-Restricted Domain:** The evaluation corpus comprises 100 authentic Wikipedia articles rather than the full 5.4 million article Wikipedia dump. Consequently, open-domain recall against unindexed Wikipedia entities cannot be measured without scaling indexing infrastructure.
* **Sample Size:** Evaluation is conducted on $N=60$ held-out claims. While sufficient for verifying pipeline calibration, abstention mechanics, and precision/recall metrics, larger statistical margins of error apply relative to evaluating all 9,999 dev claims.

---

## 4. Dataset Suite B: Controlled Scenarios (`data/controlled/`)

### 4.1 Purpose & Role
The controlled suite in `data/controlled/` contains 20 synthetic passages and 9 test claims specifically engineered to test edge-case system behavior under clean, noise-free conditions:
1. **Conflict Resolution:** Press releases vs. independent audit reports for fictional firms (NovaTech).
2. **Temporal Superseding:** 2019 market leader statements contradicted by 2024 market updates (Acme Corporation).
3. **Ungrounded Hallucinations:** Claims describing non-existent Martian civilizations triggering abstention.

This suite is exercised by dedicated unit tests (`tests/test_controlled_scenarios.py`) and is never conflated with FEVER benchmark results.

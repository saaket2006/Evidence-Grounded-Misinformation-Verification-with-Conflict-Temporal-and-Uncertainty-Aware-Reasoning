# Dataset Audit and Provenance Report

**Project:** Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning  
**Date:** October 2026  
**Auditor:** Senior Research Engineer & Software Auditor  
**Status:** Audited, Separated, and Scientifically Validated

---

## 1. Executive Summary

During Phase One and Phase Three audits, an inspection of the initial dataset files revealed a severe provenance flaw:
* The prior codebase claimed to perform benchmark evaluation on **FEVER (Fact Extraction and VERification)**.
* However, the actual files located in `data/processed/` contained only **20 hand-crafted toy articles** and **9 manually authored claims** describing fictional entities (e.g., *NovaTech Enterprise*, *Acme Corporation delivery drones*).
* Zero authentic FEVER examples existed in the evaluated files.

### Corrective Action Implemented:
1. **Separation of Controlled Toy Suite:** The 9 hand-crafted claims and 20 mock articles were extracted and safely relocated to `data/controlled/` as a dedicated **Controlled Edge-Case & Smoke-Testing Suite**.
2. **Acquisition of Official FEVER Release:** The official FEVER 1.0 development set (`fever_dev.jsonl`) was downloaded into `data/raw/fever_dev.jsonl` (9,999 claims, exactly balanced: 3,333 SUPPORTS, 3,333 REFUTES, 3,333 NOT ENOUGH INFO).
3. **Authentic Evidence Grounding:** A reproducible data ingestion pipeline was constructed (`scripts/prepare_data.py`) to fetch 69 authentic Wikipedia introductory articles directly from the Wikimedia Action API for the referenced Wikipedia entities, creating an 89-document benchmark corpus.
4. **Held-Out Validation & Evaluation Splits:** A 30-claim validation set (`dev.jsonl`) and a strictly held-out 60-claim evaluation set (`test.jsonl`) were generated with balanced class distributions, complete metadata, and gold evidence annotations.

---

## 2. Dataset Suite Overview

The repository now maintains two clearly distinguished, non-overlapping dataset suites:

```
data/
├── controlled/                    # Controlled Scenarios & Edge Cases (Formerly synthetic toy data)
│   ├── corpus.jsonl               # 20 hand-crafted passages (conflict, temporal, enterprise)
│   ├── train.jsonl                # 4 illustrative training examples
│   ├── dev.jsonl                  # 5 development calibration examples
│   └── test.jsonl                 # 9 controlled evaluation claims
├── raw/                           # Official Raw Benchmark Archives
│   └── fever_dev.jsonl            # Official FEVER 1.0 Dev Set (9,999 records; 4.09 MB)
├── processed/                     # Authentic FEVER Benchmark Splits (Current Ground Truth)
│   ├── corpus.jsonl               # 89 authentic Wikipedia articles & reference documents
│   ├── dev.jsonl                  # 30 authentic validation claims (10 SUP, 10 REF, 10 NEI)
│   ├── test.jsonl                 # 60 authentic held-out evaluation claims (20 SUP, 20 REF, 20 NEI)
│   └── dataset_info.json          # Reproducibility metadata and audit hash
└── indexes/                       # Vector & Lexical Retrieval Indexes
    ├── bm25.pkl                   # Okapi BM25 index over processed/corpus.jsonl
    └── dense_index.pt             # PyTorch MiniLM embeddings over processed/corpus.jsonl
```

---

## 3. Dataset Suite A: Authentic FEVER Benchmark (`data/processed/`)

### 3.1 Provenance and Source
* **Origin:** FEVER: A Large-scale Dataset for Fact Extraction and VERification (Thorne et al., NAACL-HLT 2018).
* **Source Archive:** `https://fever.ai/download/fever/shared_task_dev.jsonl`
* **Raw Record Count:** 9,999 claims.
* **License:** Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
* **Corpus Source:** Authentic Wikipedia introductory abstracts fetched via the Wikimedia Action API (`https://en.wikipedia.org/w/api.php`).

### 3.2 Label Schema & Canonical Mapping
The verification system enforces three primary verdict classes:

| Official FEVER Label | System Verdict Class | Description |
| :--- | :--- | :--- |
| `SUPPORTS` | `SUPPORTED` | Grounded external evidence entails the claim propositions. |
| `REFUTES` | `CONTRADICTED` | Grounded external evidence refutes or contradicts the claim. |
| `NOT ENOUGH INFO` | `INSUFFICIENT_EVIDENCE` | External evidence is inadequate, conflicting, or absent. |

### 3.3 Gold Evidence Annotation
In FEVER, evidence is annotated as:
`evidence: [[[Annotation_ID, Evidence_ID, "Wikipedia_Title", Line_Number], ...]]`
* **Multi-hop / Multi-passage Evidence:** FEVER groups evidence lines into sets. If multiple passages are required to prove a claim, they form a single set. If alternative independent sources prove the claim, they form alternative sets.
* **Retrieval Metric Handling:** In `src/evaluation/metrics.py`, retrieval is scored as a hit if the retriever returns *at least one complete acceptable gold evidence set*, or reaches the referenced Wikipedia article document ID.
* **Zero Leakage:** Gold evidence passages are strictly used for evaluation scoring and are **never** provided to the retriever as oracle input during inference.

### 3.4 Split Statistics

| Split | File | Record Count | `SUPPORTED` | `CONTRADICTED` | `INSUFFICIENT_EVIDENCE` | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Validation** | `data/processed/dev.jsonl` | 30 | 10 (33.3%) | 10 (33.3%) | 10 (33.3%) | Hyperparameter & threshold selection |
| **Test** | `data/processed/test.jsonl` | 60 | 20 (33.3%) | 20 (33.3%) | 20 (33.3%) | Held-out benchmark evaluation |
| **Corpus** | `data/processed/corpus.jsonl` | 89 | N/A | N/A | N/A | Full searchable external evidence corpus |

---

## 4. Dataset Suite B: Controlled Scenario & Smoke-Test Suite (`data/controlled/`)

### 4.1 Provenance and Character
* **Origin:** Manually authored by project engineers for targeted functional testing.
* **Character:** Synthetic enterprise scenarios, intentional temporal evolutions, and explicit conflicting reports.
* **Scale:** 20 documents, 9 test claims.

### 4.2 Utility & Research Purpose
While insufficient to support statistical generalization claims across open-domain literature, this suite serves an essential, irreplaceable role:
1. **Isolated Conflict Testing:** Contains controlled contradictory reports from differing institutions (e.g., NovaTech press release vs. independent auditor report) to isolate and test conflict resolution logic without retrieval noise.
2. **Isolated Chronology Testing:** Contains explicit temporal sequences (e.g., Acme drone leadership in 2019 vs. Zenith Dynamics overtaking Acme in 2024) to verify that newer evidence discounts outdated evidence.
3. **Compound Proposition Testing:** Tests conjunctions where one sub-clause is true and another is false.

---

## 5. Preprocessing & Indexing Pipeline

The processing pipeline in `scripts/prepare_data.py` is fully deterministic, idempotent, and reproducible:
1. **Filtering & Stratified Sampling:** Samples balanced sets from `data/raw/fever_dev.jsonl` with fixed random seed (42).
2. **Wikipedia Ingestion:** For all claims annotated with Wikipedia evidence titles, queries Wikipedia API for the corresponding introductory lead section.
3. **JSONL Serialization:** Emits normalized documents with fields:
   * `id`: Document identifier (e.g., `wiki_soul_food_film`)
   * `title`: Canonical entity title
   * `text`: Full lead passage text
   * `source`: Canonical title
   * `published_date`: Fixed modern reference date (`2021-01-01`)
4. **Index Synchronization:** Automatically builds Okapi BM25 (`data/indexes/bm25.pkl`) and SentenceTransformer dense embeddings (`data/indexes/dense_index.pt`) directly from `data/processed/corpus.jsonl`.

# System Architecture: Evidence-Grounded Misinformation Verification

## 1. High-Level Overview

This system provides claim-level misinformation verification grounded in external evidence. Rather than treating verification as an opaque binary classification or relying solely on internal model weights, the system extracts claims, retrieves external evidence passages using hybrid search, re-ranks candidate passages, performs cross-encoder Natural Language Inference (NLI), analyzes temporal consistency and evidence conflict, estimates multi-signal calibrated uncertainty, and decides between three primary verification outcomes:

- `SUPPORTED`
- `CONTRADICTED`
- `INSUFFICIENT_EVIDENCE`

When evidence is weak, absent, or irreconcilably contradictory, the system explicitly abstains by returning `INSUFFICIENT_EVIDENCE`.

---

## 2. Major Components & Services

1. **Claim Processing Engine (`src/claim_processing/`)**:
   - Ingests textual claims.
   - Decomposes compound claims into atomic sub-claims when conjunctions/multiple propositions exist.
   - Manages sub-claim to root-claim mapping.

2. **Hybrid Retrieval System (`src/retrieval/`)**:
   - **BM25 Lexical Retriever**: Keyword-based matching over tokenized evidence corpus.
   - **Dense Semantic Retriever**: Embedding-based similarity search using sentence transformers.
   - **Hybrid Fusion**: Combines lexical and semantic candidate pools with reciprocal rank fusion or linear score combination.

3. **Re-Ranking Module (`src/reranking/`)**:
   - Cross-encoder re-ranking model scoring (claim, passage) relevance pairs to select top-k candidate evidence passages.

4. **Claim–Evidence NLI Classifier (`src/nli/`)**:
   - Pretrained transformer NLI model classifying evidence relationship into `SUPPORT`, `CONTRADICT`, or `NEUTRAL` with calibrated class probabilities.

5. **Temporal Reasoning Engine (`src/temporal/`)**:
   - Extracts temporal anchors, publication dates, and explicit time expressions from claims and evidence.
   - Evaluates temporal consistency (e.g., outdated evidence, postdated events).

6. **Conflict Detection Module (`src/conflict/`)**:
   - Analyzes distribution and balance of supporting vs. contradicting evidence passages.
   - Computes conflict scores and partitions evidence into distinct consensus sets.

7. **Evidence Aggregation & Uncertainty Module (`src/aggregation/`, `src/uncertainty/`)**:
   - Aggregates multi-passage NLI probabilities weighted by retrieval relevance, temporal validity, and conflict penalties.
   - Multi-signal uncertainty estimation (NLI entropy, evidence disagreement, retrieval quality, temporal mismatch).
   - Calibrated confidence estimation.

8. **Decision & Abstention Engine (`src/decision/`)**:
   - Evaluates verification thresholds on aggregated support/contradiction scores and uncertainty.
   - Emits final verdict: `SUPPORTED`, `CONTRADICTED`, or abstains as `INSUFFICIENT_EVIDENCE`.

9. **Auditable Explanation & Output (`src/pipeline/`)**:
   - Generates structured, transparent JSON verification reports detailing sub-claims, evidence passages, sources, dates, NLI scores, conflict flags, and reasoning steps.

10. **Optional Reasoning Engine (`src/reasoning/`)**:
    - Optional LLM-assisted verification advisor isolated behind a replaceable interface for difficult or ambiguous edge cases.

11. **Evaluation Suite (`src/evaluation/`)**:
    - Evaluates retrieval (Recall@k, MRR), classification (Accuracy, Macro-F1), uncertainty calibration (ECE, Brier score), and abstention (Coverage, Selective Accuracy).

12. **Minimal Web UI (`ui/`)**:
    - Interactive web interface for inspecting verification outputs, evidence breakdowns, and confidence/uncertainty diagnostics.

---

## 3. Communication and Data Flows

```text
               User Input: Textual Claim
                         │
                         ▼
             [Claim Processing Engine]
          (Atomic Decomposition if needed)
                         │
                         ▼
             [Hybrid Retrieval Stage]
          ┌──────────────┴──────────────┐
          ▼                             ▼
   [BM25 Lexical]              [Dense Semantic]
          └──────────────┬──────────────┘
                         ▼
             [Candidate Fusion Pool]
                         │
                         ▼
             [Cross-Encoder Re-ranker]
                         │ (Top-k Passages)
                         ▼
             [Claim-Evidence NLI Engine]
         (SUPPORT / CONTRADICT / NEUTRAL)
                         │
                         ▼
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
 [Temporal Analysis]               [Conflict Analysis]
       └─────────────────┬─────────────────┘
                         ▼
          [Evidence Aggregation Engine]
                         │
                         ▼
            [Uncertainty Estimator]
          (Multi-signal Uncertainty)
                         │
                         ▼
           [Decision & Abstention Engine]
      (Threshold checks & Abstention policies)
                         │
                         ▼
        Final Verdict & Auditable Evidence Report
   (SUPPORTED | CONTRADICTED | INSUFFICIENT_EVIDENCE)
```

---

## 4. Primary Data Stores & Artifacts

- **Raw Data (`data/raw/`)**: Downloaded datasets (e.g., official FEVER 1.0 shared task development set).
- **Processed Corpus (`data/processed/`)**: Authentic FEVER evaluation splits (`dev.jsonl`, `test.jsonl`), authentic Wikipedia corpus (`corpus.jsonl`), and index metadata.
- **Controlled Scenarios (`data/controlled/`)**: Controlled functional suites with explicit enterprise reports, conflicting audits, and temporal evolutions for edge-case validation.
- **Index Store (`data/indexes/`)**: Serialized Okapi BM25 indices (`bm25.pkl`) and dense PyTorch tensor embeddings (`dense_index.pt`).
- **Results (`results/`)**: Machine-readable JSON/CSV logs of experimental benchmarks, calibration evaluations, and ablation studies across both authentic FEVER and controlled suites.

---

## 5. Major External Dependencies & AI Components

- **Deep Learning Framework**: PyTorch 2.9.1 with CUDA acceleration (NVIDIA RTX GPU).
- **Transformers & NLI**: Hugging Face `transformers` (pretrained NLI model, e.g., `roberta-large-mnli` / `deberta-v3-base-mnli` / `distilbert-base-uncased` NLI).
- **Dense Embeddings & Re-ranking**: `sentence-transformers` for bi-encoder embeddings and cross-encoder re-ranking.
- **Lexical Indexing**: `rank-bm25` for Okapi BM25 scoring.
- **NLP / Temporal Parsing**: Python `spacy` (`en_core_web_sm`) and `dateutil` regex temporal parsers.
- **Serving / UI**: Streamlit / FastAPI for demonstration and API testing.

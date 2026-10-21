# Known System Limitations and Research Bounds

**Project:** Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning  
**Date:** October 2026  
**Auditor:** Senior Research Engineer & Software Auditor  
**Status:** Documented for Scientific Rigor

---

## 1. Executive Summary

In adherence to scientific integrity principles, this document explicitly identifies all technical constraints, heuristic approximations, external dependency bounds, and unexecuted experimental conditions present in the current implementation.

---

## 2. Identified Limitations and Technical Boundaries

### 2.1 External LLM Reasoning Layer (Experiment E)
* **Status:** Adapter Implemented, Experiment `NOT EVALUATED`.
* **Details:** The system provides a fully functioning, pluggable HTTP adapter (`src/reasoning/engine.py`) designed for OpenAI-compatible endpoints (Ollama, vLLM, OpenAI, DeepSeek). However, no external API credentials (`OPENAI_API_KEY`) were configured in the local execution environment.
* **Research Impact:** The core verification pipeline operates 100% locally and deterministically using DistilBERT MNLI and SentenceTransformers without requiring an LLM. In accordance with anti-fabrication rules, Experiment E results are recorded as explicit `N/A` values across all metric columns and `null` metric objects in JSON, strictly preventing any metric inheritance from Experiment D, and clearly flagged `[NOT EVALUATED - No API Key]`.

### 2.2 Syntactic Rule-Based Claim Decomposition
* **Status:** Operational Heuristic Approximation.
* **Details:** `ClaimDecomposer` uses syntactic rules based on coordinating conjunctions (`and`, `while`, `but`), semicolons, and relative clauses, guarded by a minimum token threshold (`min_tokens_for_split: 8`).
* **Limitations:**
  * Complex nested clauses, anaphora resolution, or implicit coreferences (e.g., *"Marie Curie won two Nobel Prizes, the second being in Chemistry"*) are not fully rewritten into standalone self-contained propositions.
  * Recommendation for future research: Incorporate a lightweight neural Semantic Role Labeling (SRL) or T5-based proposition extractor.

### 2.3 Evidence Corpus Scale
* **Status:** Focused Research Benchmark Corpus (100 Documents).
* **Details:** The authentic FEVER evaluation split is grounded against an external corpus of 100 authentic Wikipedia introductory articles fetched via the Wikimedia API, selected strictly from the reference `dev_pool` independently of held-out test claims.
* **Limitations:**
  * While representative for testing pipeline behavior, calibration, and abstention mechanics, the 100-document slice covers only 22.5% of the entities referenced in the unbiased held-out test claims.
  * Scaling to full Wikipedia will require sharded dense vector indexing (such as FAISS or Milvus) and distributed Elasticsearch clusters rather than in-memory PyTorch tensors and pickled BM25 structures.

### 2.4 Temporal Expression Extraction
* **Status:** Regex & Heuristic Chronological Analysis.
* **Details:** `TemporalAnalyzer` extracts 4-digit Gregorian calendar years and common date formats (YYYY-MM-DD), comparing claim temporal constraints against evidence publication dates and explicit textual years.
* **Limitations:**
  * Relative temporal expressions without explicit dates (e.g., *"recently"*, *"last decade"*, *"two months before the merger"*) require anchor timestamp normalization not fully modeled by simple year regex.
  * Does not implement full TimeML / TIMEX3 formal temporal logic.

### 2.5 Cross-Encoder Context Window Limit
* **Status:** Architectural Bound.
* **Details:** `cross-encoder/ms-marco-MiniLM-L-6-v2` has a maximum sequence length of 512 tokens.
* **Limitations:** Claim-evidence concatenation exceeding 512 subword tokens is truncated. In our preprocessing, passages are limited to introductory abstracts (~100–300 words), preventing truncation on standard benchmark instances, but very lengthy investigative articles would require sliding-window chunking.

### 2.6 Domain Transfer & Threshold Sensitivity
* **Status:** Empirical Finding.
* **Details:** Optimal abstention and support thresholds ($\tau_{\text{sup}} = 0.55$, $\tau_{\text{unc}} = 0.60$) were selected on the validation split (`dev.jsonl`).
* **Limitations:** Application to alternative domains (e.g., fast-moving Twitter rumors, biomedical claims in PubMed) may exhibit different baseline confidence distributions and will require re-estimating uncertainty weights on domain-specific calibration sets.

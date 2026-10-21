# Phase One Initial Audit Assessment

**Project:** Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning  
**Date of Audit:** October 2026  
**Auditor:** Senior ML Research Engineer & Software Auditor  
**Repository Root:** `G:\Projects\Misinformation Verification\Project\Evidence-Grounded-Misinformation-Verification-with-Conflict-Temporal-and-Uncertainty-Aware-Reasoning`

---

## 1. System & Execution Environment

| Parameter | Observed Value | Verification Status |
|:---|:---|:---:|
| **Python Version** | `3.11.0` (64-bit AMD64) | Verified |
| **Operating System** | `Windows-10` / Windows 11 Build 26300 | Verified |
| **Logical CPU Cores** | 12 | Verified |
| **System RAM** | 15.4 GB total | Verified |
| **CUDA Acceleration** | `True` (NVIDIA GeForce RTX 2050, compute capability 8.6) | Verified |
| **PyTorch Version** | `2.9.1+cu130` | Verified |
| **Dependency Manifests** | `pyproject.toml`, `requirements.txt` (15 packages) | Clean import verified |

All 15 core dependencies (`torch`, `transformers`, `sentence-transformers`, `rank-bm25`, `scikit-learn`, `scipy`, `numpy`, `pandas`, `pydantic`, `pyyaml`, `spacy`, `tqdm`, `requests`, `pytest`, `streamlit`) import successfully without binary conflicts.

---

## 2. Models & Offline Inference Verification

Three primary transformer checkpoints are utilized:

1. **Claim–Evidence NLI Model:**
   - **Configured Model:** `models/distilbert-base-uncased-mnli` (255.4 MB local weights).
   - **Configured id2label:** `{"0": "ENTAILMENT", "1": "NEUTRAL", "2": "CONTRADICTION"}`.
   - **Resolved Internal Mapping:** `{0: NLILabel.SUPPORT, 1: NLILabel.NEUTRAL, 2: NLILabel.CONTRADICT}`.
   - **Verification:** Label mapping was dynamically verified via `AutoModelForSequenceClassification` config inspection. Entailment maps to SUPPORT, Contradiction to CONTRADICT, Neutral to NEUTRAL.
   - **Offline Loading:** Verified working completely offline (`HF_HUB_OFFLINE=1`).

2. **Dense Semantic Embedding Model:**
   - **Model:** `sentence-transformers/all-MiniLM-L6-v2` (80MB).
   - **Cache/Disk Status:** Cached locally in Hugging Face cache.
   - **Offline Loading:** Verified loading in <0.3s without network access.

3. **Cross-Encoder Re-Ranking Model:**
   - **Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` (85MB).
   - **Cache/Disk Status:** Cached locally in Hugging Face cache.
   - **Offline Loading:** Verified loading in <0.3s without network access.

---

## 3. Dataset & Index State

- `data/processed/corpus.jsonl`: 20 records (4.4 KB).
- `data/processed/train.jsonl`: 4 records (744 B).
- `data/processed/dev.jsonl`: 5 records (937 B).
- `data/processed/test.jsonl`: 9 records (1.95 KB).
- `data/indexes/bm25.pkl`: 7.5 KB (indexed for the 20 documents).
- `data/indexes/dense_index.pt`: 32.9 KB (20 embeddings $\times$ 384 dimensions).
- `data/raw/`: Directory does **not** exist.

---

## 4. Findings Classified by Severity

### Critical Findings

1. **Synthetic / Curated Dataset Mislabeled as Benchmark Evaluation (P0)**
   - **Finding:** The processed files under `data/processed/` contain exclusively hand-authored synthetic scenarios (e.g., Roman Atwood, Eiffel Tower, NovaTech, Acme Corp) totaling 20 passages and 9 test claims. 
   - **Issue:** The documentation (`README.md`, `Architecture.md`) and experiment logs describe these as the primary FEVER benchmark evaluation. Generalization claims cannot be substantiated on 9 hand-crafted claims.
   - **Correction Required:** 
     1. Formally isolate the curated 9 claims into `data/controlled/` for targeted functional smoke testing of conflict and temporal edge cases.
     2. Implement a reproducible benchmark acquisition pipeline downloading the official FEVER dataset (`paper_dev.jsonl`, verified live at 2.07 MB) and processing a legitimate, held-out evaluation subset with authentic evidence annotations and label mappings.

2. **Pseudo-LLM Advisory Engine in Experiment E (P0)**
   - **Finding:** In `src/reasoning/engine.py`, `LLMReasoningAdvisor.reason()` unconditionally executes `return self.fallback.reason(...)` at line 122. No model call (local or API) is executed.
   - **Issue:** Benchmark Experiment E was reported in `results/llm_assisted.json` and `results/summary_table.csv` as "Experiment E: Full System + LLM Reasoning Advisor", claiming to benchmark an LLM advisor, when it was an exact duplicate of the heuristic fallback.
   - **Correction Required:** 
     1. Correct the documentation and experiment labeling immediately.
     2. Implement a genuine, decoupled LLM adapter supporting standard OpenAI-compatible and local LLM endpoints (e.g. Ollama, Gemini, OpenAI) via environment variables.
     3. Explicitly report whether the LLM actually ran, record invocation flags, and mark experiments as `NOT EVALUATED` when API credentials or local LLM instances are unavailable.

3. **Mathematically Incorrect Brier Score Implementation (P0)**
   - **Finding:** In `src/evaluation/metrics.py`, line 97:
     ```python
     brier = float(np.mean((conf - acc) ** 2))
     ```
   - **Issue:** This computes the mean squared error between scalar confidence and a binary 0/1 accuracy indicator. The standard multiclass Brier score for a 3-class model ($\mathcal{Y} \in \{SUPPORTED, CONTRADICTED, INSUFFICIENT\_EVIDENCE\}$) is:
     $$BS = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (p_{i,k} - y_{i,k})^2$$
     where $\mathbf{p}_i$ is the predicted probability vector and $\mathbf{y}_i$ is the one-hot ground truth vector.
   - **Correction Required:** Implement the true multiclass Brier score with explicit class vector inputs and documented normalization, and retain top-label binary Brier score as a separate secondary metric if desired.

---

### High Findings

1. **Incomplete Classification & Calibration Metrics (P1)**
   - **Finding:** `compute_verification_metrics()` does not return a confusion matrix. `compute_calibration_metrics()` only computes top-label ECE across binary accuracy rather than multiclass calibration.
   - **Correction Required:** Implement a full $3 \times 3$ confusion matrix with explicit class ordering and sample support; implement structured ECE with configurable binning and explicit empty-bin handling.

2. **Missing Automated Metric Tests (P1)**
   - **Finding:** The test directory lacks `test_metrics.py`. The evaluation metrics have not been independently tested against verified numerical ground truths, edge cases (empty inputs, missing classes, zero coverage), or probability simplex constraints.
   - **Correction Required:** Create comprehensive unit tests with manually calculated expected values for accuracy, macro-F1, per-class metrics, confusion matrix, Recall@k, MRR, multiclass Brier score, and ECE.

3. **Silent Download Fallback in Data Preparation (P1)**
   - **Finding:** `scripts/download_data.py` previously failed or was bypassed without logging an error, leaving `data/raw/` empty, while `scripts/prepare_data.py` silently fell back to 18 toy claims without alerting the user that the benchmark was synthetic.
   - **Correction Required:** Require explicit dataset provenance flags and disallow silent substitution of synthetic data.

---

### Medium Findings

1. **Uncertainty Calibration Threshold Validation (P2)**
   - **Finding:** Decision thresholds (`support_threshold: 0.55`, `contradict_threshold: 0.55`, `max_uncertainty_threshold: 0.60`) were selected heuristically without calibration fitting on a distinct validation split.
   - **Correction Required:** Fit/validate abstention thresholds strictly on `dev.jsonl` and evaluate selectively on `test.jsonl` without test-set leakage.

2. **Duplicate Source Attribution in Conflict and Temporal Modules (P2)**
   - **Finding:** In `src/conflict/detector.py`, passage counting can treat multiple text snippets from the same Wikipedia article as independent corroboration.
   - **Correction Required:** Group passages by source/document ID before assessing independent corroborating consensus.

3. **Index-Corpus Hash Invalidation (P2)**
   - **Finding:** Indexes in `data/indexes/` do not verify whether `corpus.jsonl` has changed since the index was generated.
   - **Correction Required:** Add fingerprinting or index recreation validation in `build_index.py`.

---

### Low Findings

1. **Tokenization Deprecation Warnings (P3)**
   - **Finding:** Hugging Face `tokenization_bert.py:104` issues `DeprecationWarning: WordPiece.__init__ will not create from files anymore`.
   - **Correction Required:** Harmless runtime warning; suppress or configure tokenizer initialization cleanly.

2. **Git Repository Hygiene (P3)**
   - **Finding:** Large models and index artifacts must be carefully checked in `.gitignore` so weights aren't tracked while scripts and configs remain reproducible.
   - **Correction Required:** Verify `.gitignore` covers model checkpoints, cache directories, and temporary data while preserving essential configs and benchmark metadata.

---

## 5. Immediate Action Plan

1. **Phase Two:** Audit the verification pipeline end-to-end; resolve source deduplication in conflict and temporal modules.
2. **Phase Three:** Build the authentic FEVER benchmark pipeline (download `paper_dev.jsonl`, map labels, extract evidence passages, create reproducible splits), and separate the curated dataset into `data/controlled/`.
3. **Phase Four:** Implement the mathematically correct multiclass Brier score, ECE, confusion matrix, and complete unit tests in `tests/test_metrics.py`.
4. **Phase Five:** Build an authentic, pluggable LLM adapter in `src/reasoning/engine.py` with provider support, timeouts, fallback tracking, and unit tests in `tests/test_reasoning.py`.
5. **Phase Six–Eight:** Execute controlled experiments on the controlled dataset and benchmark evaluations on the authentic FEVER evaluation split.
6. **Phase Nine–Eleven:** Run the full test suite, verify end-to-end claims, update all architecture and document assets, and produce audit documentation.

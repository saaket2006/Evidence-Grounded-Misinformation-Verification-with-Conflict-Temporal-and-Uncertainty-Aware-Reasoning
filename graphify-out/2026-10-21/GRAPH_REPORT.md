# Graph Report - Evidence-Grounded-Misinformation-Verification-with-Conflict-Temporal-and-Uncertainty-Aware-Reasoning  (2026-10-21)

## Corpus Check
- 91 files · ~65,227 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 821 nodes · 1340 edges · 50 communities (46 shown, 4 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 77 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0fcf7b37`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ConflictReport
- test_metrics.py
- Product Requirements Document (PRD)
- Core Principles
- Documentation Architect
- Capabilities
- EvidencePassage
- Core Principles
- Capabilities
- BM25Retriever
- API Design Principles Implementation Playbook
- Core Principles
- RuleBasedClaimDecomposer
- Functional Requirements Document (FRD)
- CrossEncoderReranker
- Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning
- Non-Functional Requirements Document (NFRD)
- download_data.py
- ._ensure_model
- verifier.py
- Evidence-Grounded Multimodal Misinformation Verification with Uncertainty-Aware Reasoning
- 3. Detailed Stage Audits
- 3. Functional Software Requirements
- build_index.py
- .__init__
- SRS.md
- CorpusManager
- API Design Principles
- 13. BERT-Based Evidence Analysis Module
- System Architecture: Evidence-Grounded Misinformation Verification
- 4. Differentiating Verification Requirements
- 10. Testing Requirements
- .get_document
- 1. Introduction
- 5. Data Requirements
- download_model.py
- 2. Overall System Description
- rules/graphify.md
- workflows/graphify.md
- src/__init__.py
- Dataset Audit and Provenance Report
- misinfo-verification
- Experimental Validation Report
- prepare_data.py
- Phase One Initial Audit Assessment
- 2. Identified Limitations and Technical Boundaries
- test_end_to_end.py
- .__init__
- setup_logger

## God Nodes (most connected - your core abstractions)
1. `EvidencePassage` - 77 edges
2. `ConflictReport` - 38 edges
3. `MisinformationVerifier` - 37 edges
4. `AggregationResult` - 35 edges
5. `TemporalReport` - 29 edges
6. `Product Requirements Document (PRD)` - 24 edges
7. `Verdict` - 23 edges
8. `BM25Retriever` - 23 edges
9. `DenseRetriever` - 23 edges
10. `CorpusManager` - 22 edges

## Surprising Connections (you probably didn't know these)
- `build_indexes()` --calls--> `BM25Retriever`  [EXTRACTED]
  scripts/build_index.py → src/retrieval/bm25.py
- `build_indexes()` --calls--> `CorpusManager`  [EXTRACTED]
  scripts/build_index.py → src/retrieval/corpus.py
- `build_indexes()` --calls--> `DenseRetriever`  [EXTRACTED]
  scripts/build_index.py → src/retrieval/dense.py
- `evaluate()` --calls--> `MisinformationVerifier`  [EXTRACTED]
  scripts/evaluate.py → src/pipeline/verifier.py
- `run_experiment()` --calls--> `MisinformationVerifier`  [EXTRACTED]
  scripts/run_experiments.py → src/pipeline/verifier.py

## Import Cycles
- None detected.

## Communities (50 total, 4 thin omitted)

### Community 0 - "ConflictReport"
Cohesion: 0.06
Nodes (68): Enum, AggregationResult, BaseModel, Evidence aggregation engine synthesizing multiple evidence passages., Evidence aggregation module., ConflictReport, BaseModel, Conflict detection and consensus analysis across evidence passages. (+60 more)

### Community 1 - "test_metrics.py"
Cohesion: 0.10
Nodes (36): evaluate(), main(), Run standalone evaluation on a dataset split and export metrics., load_dataset(), main(), Any, Path, Run the full benchmark experimental suite (Experiments A, B, C, D, E). Outputs… (+28 more)

### Community 2 - "Product Requirements Document (PRD)"
Cohesion: 0.05
Nodes (37): 10. Source and Evidence Assessment, 11. Temporal Verification, 12. Contradiction-Aware Verification, 13. Multimodal Verification, 14. Uncertainty and Abstention, 15. Verification Audit Trail, 16. Product Differentiation, 17. Research-Oriented Requirements (+29 more)

### Community 3 - "Core Principles"
Cohesion: 0.06
Nodes (33): 10. Content and microcopy, 11. Feedback and error recovery, 12. Data-heavy interfaces, 13. Animation and interaction, 1. Understand, 1. Understand the user and the task, 2. Prioritize usability, 2. Structure (+25 more)

### Community 4 - "Documentation Architect"
Cohesion: 0.06
Nodes (32): 1. Documentation must reflect reality, 2. Optimize for usefulness, not length, 3. Start with the audience and purpose, 4. Use progressive disclosure, 5. Explain important "why", Architecture, Architecture Documentation, Code References (+24 more)

### Community 5 - "Capabilities"
Cohesion: 0.06
Nodes (31): API Contract & Documentation, API Design & Patterns, API Gateway & Load Balancing, Asynchronous Processing, Authentication & Authorization, Backend Architect, Behavioral Traits, Caching Strategies (+23 more)

### Community 6 - "EvidencePassage"
Cohesion: 0.05
Nodes (40): EvidenceAggregator, Synthesizes passage-level NLI classifications into a coherent claim-level…, ConflictDetector, Analyzes evidence pool for contradictory and opposing claims., Args: balance_threshold: Minimum ratio of minority-to-majority mass to declare…, BaseNLIClassifier, ABC, Base interface for Natural Language Inference (NLI) classifiers. (+32 more)

### Community 7 - "Core Principles"
Cohesion: 0.08
Nodes (24): 1. Start with requirements, 2. Prefer simplicity, 3. Evaluate technology choices rationally, 4. Design for data integrity, 5. Design schemas around actual access patterns, 6. Treat migrations as production changes, 7. Scale only when justified, 8. Consider the whole system (+16 more)

### Community 8 - "Capabilities"
Cohesion: 0.09
Nodes (22): Application Security Testing, Behavioral Traits, Capabilities, Cloud Security, Compliance & Governance, DevSecOps & Security Automation, Do not use this skill when, Emerging Security Technologies (+14 more)

### Community 9 - "BM25Retriever"
Cohesion: 0.15
Nodes (21): Path, BaseRetriever, ABC, Base interface for evidence retrieval components., Abstract base class for evidence retrieval engines., BM25Retriever, Lexical BM25 retrieval engine., Lexical retriever based on Okapi BM25. (+13 more)

### Community 10 - "API Design Principles Implementation Playbook"
Cohesion: 0.10
Nodes (19): 1. RESTful Design Principles, 2. GraphQL Design Principles, 3. API Versioning Strategies, API Design Principles Implementation Playbook, Best Practices, Common Pitfalls, Core Concepts, GraphQL APIs (+11 more)

### Community 11 - "Core Principles"
Cohesion: 0.10
Nodes (19): 10. Testing, 11. SEO, 1. Follow the existing project architecture, 2. Build for correctness first, 3. Component design, 4. State and data fetching, 5. Responsive design, 6. Accessibility (+11 more)

### Community 12 - "RuleBasedClaimDecomposer"
Cohesion: 0.16
Nodes (12): BaseClaimDecomposer, ABC, Claim processing and atomic proposition decomposition., Abstract interface for claim decomposition., Decompose a textual claim into atomic subclaims., Deterministic rule-based claim decomposer. Splits compound propositions on…, RuleBasedClaimDecomposer, Claim processing module. (+4 more)

### Community 13 - "Functional Requirements Document (FRD)"
Cohesion: 0.11
Nodes (18): 10. Audit Trail, 11. Verification Report, 12. Adaptive Verification, 13. Error Handling, 14. Research Support, 15. BERT-Based Evidence Analysis Requirements, 15. Research-Differentiating Functional Requirements, 1. Functional Scope (+10 more)

### Community 14 - "CrossEncoderReranker"
Cohesion: 0.15
Nodes (12): CrossEncoder, BaseReranker, ABC, Base interface for evidence re-ranking., Re-rank candidate evidence passages relative to the query. Args: query: Claim…, Abstract interface for passage re-ranking., CrossEncoderReranker, Cross-encoder re-ranking engine for candidate evidence passages. (+4 more)

### Community 15 - "Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning"
Cohesion: 0.10
Nodes (20): 10. Audit Documentation Suite, 10. Evaluation Metrics, 11. Configuration Guide, 12. Running Tests, 13. Limitations & Future Work, 1. Problem Statement, 2. Proposed Solution, 3. High-Level Architecture (+12 more)

### Community 16 - "Non-Functional Requirements Document (NFRD)"
Cohesion: 0.12
Nodes (16): 10. Maintainability, 11. Research Reproducibility, 12. Ethical and Responsible Behavior, 13. BERT Component Quality Requirements, 13. Research Differentiation Quality Requirements, 1. Purpose, 2. Reliability, 3. Accuracy and Verification Quality (+8 more)

### Community 17 - "download_data.py"
Cohesion: 0.47
Nodes (5): download_file(), main(), Path, Download FEVER dataset files or create verified benchmark subsets. Supports…, Download a file with fallback handling.

### Community 18 - "._ensure_model"
Cohesion: 0.29
Nodes (4): SentenceTransformer, Lazy load the sentence transformer model., Encode all documents in the corpus and build dense tensor index., Search dense embeddings using cosine similarity.

### Community 19 - "verifier.py"
Cohesion: 0.12
Nodes (18): main(), CLI entry point to verify a single claim using the verification pipeline., Script to verify and inspect representative end-to-end claims across all…, run_representative_inspections(), BaseModel, Structured data models for the verification pipeline., SubClaim, VerificationResult (+10 more)

### Community 20 - "Evidence-Grounded Multimodal Misinformation Verification with Uncertainty-Aware Reasoning"
Cohesion: 0.15
Nodes (12): Adaptive Verification with BERT, BERT's Role in the Proposed Methodology, Evidence-Grounded Multimodal Misinformation Verification with Uncertainty-Aware Reasoning, Final Project Positioning, Literature Alignment and Research Gap, Methodological Differentiation, Methodological Stages, Methodology (+4 more)

### Community 21 - "3. Detailed Stage Audits"
Cohesion: 0.10
Nodes (19): 1. Executive Summary, 2. Component-by-Component Implementation Mapping, 3.10 Calibrated Uncertainty Estimation, 3.11 Decision Engine & Selective Abstention, 3.12 LLM Reasoning Advisor, 3.1 Claim Decomposition, 3.2 Lexical Retrieval (BM25), 3.3 Dense Semantic Retrieval (+11 more)

### Community 22 - "3. Functional Software Requirements"
Cohesion: 0.17
Nodes (12): 3.10 Reporting Module, 3.11 Audit Module, 3.1 Input Module, 3.2 Claim Processing Module, 3.3 Retrieval Module, 3.4 Evidence Assessment Module, 3.5 Temporal Module, 3.6 Multimodal Module (+4 more)

### Community 23 - "build_index.py"
Cohesion: 0.19
Nodes (10): cache_resource, build_indexes(), main(), Build and save BM25 and Dense retrieval indexes from processed corpus., load_config(), Path, Configuration management module., Load configuration from a YAML file. Args: config_path: Path to the YAML… (+2 more)

### Community 24 - ".__init__"
Cohesion: 0.18
Nodes (7): Path, Simple alphanumeric lowercasing tokenizer for BM25., Build BM25 index from corpus manager documents., Save BM25 index and doc_ids to disk., Load precomputed BM25 index from disk., Search BM25 index for the given query., tokenize()

### Community 25 - "SRS.md"
Cohesion: 0.20
Nodes (9): 11. Traceability, 12. Open Design Decisions, 13. Current Research Differentiation Statement, 5. External System Requirements, 6. Security Requirements, 7. Performance Requirements, 9. Research and Evaluation Requirements, Project Title (+1 more)

### Community 26 - "CorpusManager"
Cohesion: 0.25
Nodes (6): CorpusManager, Path, Manages passage loading, lookup, and metadata for the evidence corpus., Load corpus JSONL into memory., corpus_manager(), fixture

### Community 27 - "API Design Principles"
Cohesion: 0.25
Nodes (7): API Design Principles, Description:, Do not use this skill when, Instructions, Name: api-design-principles, Resources, Use this skill when

### Community 28 - "13. BERT-Based Evidence Analysis Module"
Cohesion: 0.25
Nodes (8): 13.1 Purpose, 13.2 Functional Requirements, 13.3 Interaction with the LLM, 13.4 Adaptive Verification, 13.5 BERT Ablation, 13.6 Model Selection, 13.7 Research Boundary, 13. BERT-Based Evidence Analysis Module

### Community 29 - "System Architecture: Evidence-Grounded Misinformation Verification"
Cohesion: 0.29
Nodes (6): 1. High-Level Overview, 2. Major Components & Services, 3. Communication and Data Flows, 4. Primary Data Stores & Artifacts, 5. Major External Dependencies & AI Components, System Architecture: Evidence-Grounded Misinformation Verification

### Community 30 - "4. Differentiating Verification Requirements"
Cohesion: 0.29
Nodes (7): 4.1 Conflict-Aware Evidence Model, 4.2 Temporal Assessment, 4.3 Uncertainty and Abstention, 4.4 Adaptive Verification, 4.5 M-RAV Baseline Boundary, 4.6 LLM Role, 4. Differentiating Verification Requirements

### Community 31 - "10. Testing Requirements"
Cohesion: 0.33
Nodes (6): 10. Testing Requirements, Failure Testing, Integration Testing, Research Evaluation, Robustness Testing, Unit Testing

### Community 32 - ".get_document"
Cohesion: 0.40
Nodes (3): Any, Retrieve document by ID., Convert a document into a pipeline EvidencePassage object.

### Community 33 - "1. Introduction"
Cohesion: 0.50
Nodes (4): 1.1 Purpose, 1.2 Scope, 1.3 Definitions, 1. Introduction

### Community 34 - "5. Data Requirements"
Cohesion: 0.50
Nodes (4): 4.1 Claim Record, 4.2 Evidence Record, 4.3 Verification Record, 5. Data Requirements

### Community 35 - "download_model.py"
Cohesion: 0.67
Nodes (3): download_with_progress(), main(), Helper to download model files with resume support and progress logging.

### Community 36 - "2. Overall System Description"
Cohesion: 0.67
Nodes (3): 2.1 Product Perspective, 2.2 User Classes, 2. Overall System Description

### Community 40 - "Dataset Audit and Provenance Report"
Cohesion: 0.14
Nodes (13): 1. Executive Summary, 2. Dataset Suite Overview, 3.1 Provenance and Source, 3.2 Label Schema & Canonical Mapping, 3.3 Gold Evidence Annotation, 3.4 Split Statistics, 3. Dataset Suite A: Authentic FEVER Benchmark (`data/processed/`), 4.1 Provenance and Character (+5 more)

### Community 43 - "Experimental Validation Report"
Cohesion: 0.14
Nodes (13): 1.1 Evaluated Ablation Pipeline, 1.2 Mathematical Metric Formulations, 1. Experimental Methodology and Setup, 2. Benchmark Evaluation on Authentic FEVER Test Split ($N=60$), 3. Benchmark Evaluation on Controlled Scenarios ($N=9$), 4.1 Value of Evidence Grounding (A vs. B), 4.2 Impact of Conflict and Temporal Logic (B vs. C), 4.3 Proven Efficacy of Uncertainty-Aware Abstention (C vs. D) (+5 more)

### Community 44 - "prepare_data.py"
Cohesion: 0.22
Nodes (13): decode_fever_title(), fetch_wikipedia_articles(), main(), prepare_controlled_suite(), prepare_fever_benchmark(), Path, Preprocess datasets and construct reproducible benchmark and controlled suites.…, Decode FEVER title encoding (-LRB-, -RRB-, underscores). (+5 more)

### Community 45 - "Phase One Initial Audit Assessment"
Cohesion: 0.18
Nodes (10): 1. System & Execution Environment, 2. Models & Offline Inference Verification, 3. Dataset & Index State, 4. Findings Classified by Severity, 5. Immediate Action Plan, Critical Findings, High Findings, Low Findings (+2 more)

### Community 46 - "2. Identified Limitations and Technical Boundaries"
Cohesion: 0.20
Nodes (9): 1. Executive Summary, 2.1 External LLM Reasoning Layer (Experiment E), 2.2 Syntactic Rule-Based Claim Decomposition, 2.3 Evidence Corpus Scale, 2.4 Temporal Expression Extraction, 2.5 Cross-Encoder Context Window Limit, 2.6 Domain Transfer & Threshold Sensitivity, 2. Identified Limitations and Technical Boundaries (+1 more)

### Community 47 - "test_end_to_end.py"
Cohesion: 0.25
Nodes (3): fixture, End-to-end integration tests for the full verification pipeline., verifier()

### Community 48 - ".__init__"
Cohesion: 0.40
Nodes (3): Path, Save embeddings and document IDs to disk., Load embeddings and document IDs from disk.

### Community 49 - "setup_logger"
Cohesion: 0.67
Nodes (3): Logger, Configure and return a structured logger., setup_logger()

## Knowledge Gaps
- **353 isolated node(s):** `misinfo-verification`, `graphify`, `Description:`, `Use this skill when`, `Do not use this skill when` (+348 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EvidencePassage` connect `EvidencePassage` to `ConflictReport`, `.get_document`, `BM25Retriever`, `CrossEncoderReranker`, `._ensure_model`, `verifier.py`, `.__init__`, `CorpusManager`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `MisinformationVerifier` connect `verifier.py` to `ConflictReport`, `test_metrics.py`, `EvidencePassage`, `BM25Retriever`, `RuleBasedClaimDecomposer`, `CrossEncoderReranker`, `test_end_to_end.py`, `build_index.py`, `CorpusManager`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `DenseRetriever` connect `BM25Retriever` to `EvidencePassage`, `.__init__`, `._ensure_model`, `verifier.py`, `build_index.py`, `CorpusManager`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `EvidencePassage` (e.g. with `AggregationResult` and `EvidenceAggregator`) actually correct?**
  _`EvidencePassage` has 22 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `ConflictReport` (e.g. with `EvidencePassage` and `NLILabel`) actually correct?**
  _`ConflictReport` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `MisinformationVerifier` (e.g. with `EvidenceAggregator` and `RuleBasedClaimDecomposer`) actually correct?**
  _`MisinformationVerifier` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 9 inferred relationships involving `AggregationResult` (e.g. with `EvidencePassage` and `NLILabel`) actually correct?**
  _`AggregationResult` has 9 INFERRED edges - model-reasoned connections that need verification._
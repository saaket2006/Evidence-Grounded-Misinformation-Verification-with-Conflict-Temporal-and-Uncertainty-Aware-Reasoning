# Software Requirements Specification (SRS)

## Project Title
**Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning**

**Version:** 0.2 — Stress-Verified Draft  
**Status:** Draft

# 1. Introduction

## 1.1 Purpose
Define software requirements for a system that analyzes factual claims, retrieves and assesses evidence, reasons over supporting and contradicting information, considers temporal and multimodal consistency, and produces uncertainty-aware, auditable verification results.

## 1.2 Scope
The software shall support content submission, claim extraction/decomposition, evidence retrieval, support/contradiction searches, evidence assessment, source/temporal assessment, multimodal consistency, synthesis, uncertainty, abstention, structured reports, audit trails, and research evaluation.

## 1.3 Definitions

| Term | Definition |
|---|---|
| Claim | A factual proposition that can potentially be verified. |
| Evidence | External information used to assess a claim. |
| Supporting Evidence | Evidence supporting the claim. |
| Contradicting Evidence | Evidence challenging/disproving the claim. |
| Contextual Evidence | Information helping interpret a claim without directly proving/disproving it. |
| Temporal Validity | Whether evidence is appropriate for the relevant time context. |
| Abstention | Choosing not to issue a definitive verdict because evidence is insufficient/conflicting. |
| Audit Trail | Traceable relationship between claim, evidence, source, reasoning, confidence, and verdict. |

# 2. Overall System Description

## 2.1 Product Perspective
The system is a verification pipeline rather than a general-purpose conversational chatbot:

**Input → Claim Extraction → Claim Decomposition → Retrieval → Evidence Assessment → Temporal/Multimodal Checks → Reasoning → Uncertainty → Verification Report**

The exact implementation architecture will be defined separately.

## 2.2 User Classes
- **General User:** submits content and reviews results.
- **Researcher:** uses outputs and configurations for analysis.
- **Reviewer/Fact-Checking User:** uses evidence and uncertainty for human review.

# 3. Functional Software Requirements

## 3.1 Input Module
- **SRS-FR-01:** Accept textual claims/article text.
- **SRS-FR-02:** Support supported article URLs.
- **SRS-FR-03:** Support images.
- **SRS-FR-04:** Validate input type and size.

## 3.2 Claim Processing Module
- **SRS-FR-05:** Identify candidate factual claims.
- **SRS-FR-06:** Preserve relationship between claims and original input.
- **SRS-FR-07:** Decompose complex claims where useful.
- **SRS-FR-08:** Assign identifiers to claims.

## 3.3 Retrieval Module
- **SRS-FR-09:** Retrieve relevant evidence.
- **SRS-FR-10:** Support support-oriented queries.
- **SRS-FR-11:** Support contradiction-oriented queries.
- **SRS-FR-12:** Support contextual queries.
- **SRS-FR-13:** Retain source/retrieval metadata.

## 3.4 Evidence Assessment Module
- **SRS-FR-14:** Evaluate relevance.
- **SRS-FR-15:** Associate evidence with a relationship type.
- **SRS-FR-16:** Retain source type, authority indicators, date, and provenance when available.
- **SRS-FR-17:** Identify potential duplicated/dependent evidence.
- **SRS-FR-18:** Detect potential evidence conflicts.

## 3.5 Temporal Module
- **SRS-FR-19:** Extract temporal information where possible.
- **SRS-FR-20:** Record evidence dates where available.
- **SRS-FR-21:** Compare claim and evidence temporal context.
- **SRS-FR-22:** Generate temporal inconsistency indicators where appropriate.

## 3.6 Multimodal Module
- **SRS-FR-23:** Process relevant visual information.
- **SRS-FR-24:** Extract embedded image text where required.
- **SRS-FR-25:** Compare textual and visual information.
- **SRS-FR-26:** Identify potential cross-modal inconsistencies.

## 3.7 Verification Module
- **SRS-FR-27:** Synthesize assessed evidence.
- **SRS-FR-28:** Produce a defined verdict category.
- **SRS-FR-29:** Support Conflicting Evidence.
- **SRS-FR-30:** Support Insufficient Evidence.
- **SRS-FR-31:** Do not equate absence of retrieved evidence with contradiction without justification.

## 3.8 Uncertainty Module
- **SRS-FR-32:** Produce confidence/uncertainty representation.
- **SRS-FR-33:** Record uncertainty factors.
- **SRS-FR-34:** Support abstention.
- **SRS-FR-35:** Allow uncertainty behavior to be evaluated independently.

## 3.9 Adaptive Verification Module
- **SRS-FR-36:** Determine when additional verification is warranted.
- **SRS-FR-37:** Support additional retrieval.
- **SRS-FR-38:** Support contradiction checks for uncertain/high-risk cases.
- **SRS-FR-39:** Terminate additional verification when stopping criteria are satisfied.

## 3.10 Reporting Module
- **SRS-FR-40:** Generate structured verification reports.
- **SRS-FR-41:** Include claim-level verdicts.
- **SRS-FR-42:** Display relevant evidence.
- **SRS-FR-43:** Display available source information.
- **SRS-FR-44:** Communicate uncertainty.
- **SRS-FR-45:** Communicate major temporal/multimodal inconsistencies.

## 3.11 Audit Module
- **SRS-FR-46:** Maintain Claim → Evidence → Source → Relationship → Reasoning/Decision Factors → Confidence → Verdict.
- **SRS-FR-47:** Trace evidence to source.
- **SRS-FR-48:** Trace verdicts to considered evidence.
- **SRS-FR-49:** Retain metadata required for research analysis.
- **SRS-FR-50:** Do not expose or depend on unrestricted private chain-of-thought; expose evidence, decision factors, and verification provenance instead.

# 4. Differentiating Verification Requirements

## 4.1 Conflict-Aware Evidence Model

The evidence model shall retain at least:
- supporting evidence;
- contradicting evidence;
- contextual evidence;
- evidence quality/relevance;
- source identity;
- temporal information;
- evidence relationships.

The system shall not collapse materially conflicting evidence into a single undifferentiated evidence list.

## 4.2 Temporal Assessment

Where temporal information exists, the system shall record:
- claim time/context;
- evidence publication/event time;
- temporal compatibility;
- detected temporal mismatch.

## 4.3 Uncertainty and Abstention

The system shall distinguish:
- supported/contradicted evidence;
- conflicting evidence;
- insufficient evidence;
- model uncertainty.

A definitive verdict shall not be required when configured abstention criteria are met.

## 4.4 Adaptive Verification

The system should be able to trigger additional retrieval/reasoning when:
- evidence is insufficient;
- evidence conflicts materially;
- temporal validity is unclear;
- multimodal information is inconsistent;
- or another defined difficulty criterion is met.

## 4.5 M-RAV Baseline Boundary

An M-RAV-like baseline should be representable for evaluation. The baseline corresponds conceptually to:

> retrieve relevant evidence → multimodal alignment → relevance assessment → LLM verification

The proposed system shall be evaluated with its additional mechanisms enabled/disabled so that any improvement beyond this baseline can be attributed experimentally.

## 4.6 LLM Role

The LLM shall be treated as a reasoning/interpretation component within the verification pipeline. It shall not be treated as an unquestioned authoritative source of truth.

# 5. Data Requirements

## 4.1 Claim Record
Should contain, as applicable:
- Claim ID
- Original text
- Normalized claim
- Source content reference
- Temporal information
- Verification status
- Verdict
- Confidence/uncertainty

## 4.2 Evidence Record
Should contain:
- Evidence ID
- Claim ID
- Source
- URL/reference
- Retrieved content
- Publication date
- Retrieval timestamp
- Evidence relationship
- Relevance assessment
- Source metadata
- Temporal assessment

## 4.3 Verification Record
Should contain:
- Verification ID
- Input reference
- Claim IDs
- Evidence IDs
- Verdict
- Confidence/uncertainty
- Major factors
- Verification configuration
- Model/version metadata where required

# 5. External System Requirements
Exact external services shall be selected during architecture design. Potential categories include search/evidence retrieval, web/content extraction, language model, multimodal model, OCR, persistence, and hosting services. This SRS does not mandate a provider at this stage.

# 6. Security Requirements
- **SRS-SEC-01:** Store secrets outside source code.
- **SRS-SEC-02:** Treat retrieved content as untrusted input.
- **SRS-SEC-03:** Prevent retrieved content from overriding system verification instructions.
- **SRS-SEC-04:** Sanitize user-submitted content where required.
- **SRS-SEC-05:** Never expose credentials in reports/logs.

# 7. Performance Requirements
Exact targets shall be established through benchmarking. The system should avoid unnecessary retrieval/model calls, support adaptive verification, process claims independently where practical, and expose failures rather than silently returning incomplete conclusions.

Performance evaluation should record total latency, retrieval latency, model latency, number of retrieval operations, number of model calls, and measurable resource/cost consumption.

# 9. Research and Evaluation Requirements
The implementation shall support controlled experiments across:
- relevance-only vs. support + contradiction retrieval;
- temporal validation disabled vs. enabled;
- forced verdict vs. abstention;
- text-only vs. text + visual consistency;
- single-pass vs. adaptive/deeper verification.

Component-level ablations should permit attribution of improvements.

# 10. Testing Requirements

### Unit Testing
Claim processing, retrieval, evidence assessment, temporal processing, and reporting.

### Integration Testing
End-to-end verification.

### Failure Testing
Retrieval failures, unavailable sources, malformed input, and model/service failures.

### Research Evaluation
Benchmark datasets and controlled experiments.

### Robustness Testing
Where feasible:
- paraphrased claims;
- conflicting evidence;
- outdated evidence;
- incomplete evidence;
- misleading context;
- text-image inconsistencies.

# 11. Traceability
The implementation should maintain:

**PRD Goal → Functional Requirement → Software Requirement → Test Case → Evaluation Result**

This separates product functionality from research hypotheses and measurable experimental results.

# 12. Open Design Decisions
1. Retrieval provider(s).
2. LLM/model configuration.
3. Evidence source selection policy.
4. Source credibility methodology.
5. Temporal reasoning implementation.
6. Multimodal model selection.
7. Confidence-calibration methodology.
8. Dataset/benchmark selection.
9. Adaptive-verification stopping criteria.
10. Storage and deployment architecture.

These decisions should be justified in design/implementation documentation rather than prematurely fixed here.


---

# 13. Current Research Differentiation Statement

The software shall be designed so that the research contribution is not defined as simply implementing multimodal LLM fact-checking.

The principal comparison target is an M-RAV-like retrieve-align-verify pipeline. The proposed system is differentiated through the additional ability to:

1. seek supporting **and contradicting** evidence;
2. preserve and reason over evidence conflict;
3. validate temporal compatibility;
4. abstain under insufficient/conflicting evidence;
5. maintain an auditable evidence-to-verdict trail;
6. adapt verification depth to case difficulty;
7. treat multimodal consistency as a verification signal;
8. evaluate these mechanisms through controlled ablations.

The implementation and paper must report whether these additions actually improve the chosen metrics. They must not be assumed to be improvements merely because they are architecturally different.

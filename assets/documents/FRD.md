# Functional Requirements Document (FRD)

## Project Title
**Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning**

**Version:** 1.0 — Audited & Scientifically Validated  
**Status:** Verified Research Prototype

## 1. Functional Scope
The system provides an end-to-end workflow for submission, claim extraction, evidence retrieval and assessment, verification, uncertainty handling, auditable reporting, and selective abstention.

**Implementation Realization:**
- Textual claim verification with atomic proposition decomposition is fully delivered.
- External evidence retrieval with BM25 + Dense Hybrid search and Cross-Encoder reranking is fully delivered.
- Three-class NLI, temporal analysis, conflict detection, calibrated uncertainty, and abstention (`INSUFFICIENT_EVIDENCE`) are verified and operational.
- Input validation (text formatting, length checks) is fully implemented. Multimodal vision-language ingestion remains documented as a planned future phase.

## 2. Content Submission
- **FR-01:** Allow textual claim/article submission.
- **FR-02:** Support supported article URLs.
- **FR-03:** Support image input when relevant.
- **FR-04:** Validate submitted content before processing.

## 3. Claim Extraction and Decomposition
- **FR-05:** Identify factual claims.
- **FR-06:** Distinguish potentially verifiable factual statements from subjective/non-factual statements where feasible.
- **FR-07:** Decompose complex claims where useful.
- **FR-08:** Preserve original context for each claim.

## 4. Evidence Retrieval
- **FR-09:** Retrieve relevant external evidence.
- **FR-10:** Support supporting-evidence searches.
- **FR-11:** Support contradiction-oriented searches.
- **FR-12:** Support contextual searches.
- **FR-13:** Associate evidence with source and retrieval metadata.

## 5. Evidence Assessment
- **FR-14:** Classify evidence as supporting, contradicting, contextual, or insufficient where possible.
- **FR-15:** Assess evidence relevance.
- **FR-16:** Retain source authority/type/date/provenance when available.
- **FR-17:** Identify potential duplication or source dependence where feasible.
- **FR-18:** Detect relevant evidence conflicts.

## 6. Temporal Verification
- **FR-19:** Identify relevant temporal information in claims.
- **FR-20:** Assess evidence dates where available.
- **FR-21:** Flag temporally inappropriate evidence.

## 7. Multimodal Verification
- **FR-22:** Process relevant image information.
- **FR-23:** Compare textual and visual information.
- **FR-24:** Flag potential cross-modal inconsistency.

## 8. Verification and Reasoning
- **FR-25:** Synthesize assessed evidence.
- **FR-26:** Produce Supported, Contradicted, Misleading, Conflicting Evidence, or Insufficient Evidence.
- **FR-27:** Permit Insufficient Evidence instead of forcing a verdict.
- **FR-28:** Permit Conflicting Evidence when credible evidence cannot be reconciled.
- **FR-29:** Generate an evidence-linked explanation.

## 9. Uncertainty
- **FR-30:** Provide confidence/uncertainty.
- **FR-31:** Distinguish uncertainty arising from insufficient evidence, conflicting evidence, or reasoning where feasible.
- **FR-32:** Support abstention.

## 10. Audit Trail
- **FR-33:** Maintain Claim → Evidence → Source → Relationship → Reasoning → Confidence → Verdict.
- **FR-34:** Allow users to inspect evidence associated with a claim.
- **FR-35:** Display relevant source information.
- **FR-36:** Display the major decision factors without presenting unsupported internal reasoning as fact.

## 11. Verification Report
- **FR-37:** Generate a structured report.
- **FR-38:** Display claim-level results.
- **FR-39:** Summarize supporting, contradicting, and contextual evidence.
- **FR-40:** Communicate uncertainty and reasons.
- **FR-41:** Provide an overall assessment while retaining claim-level results.

## 12. Adaptive Verification
- **FR-42:** Identify difficult cases.
- **FR-43:** Perform additional retrieval for ambiguous/uncertain cases.
- **FR-44:** Stop additional verification when sufficient criteria are met.

## 13. Error Handling
- **FR-45:** Report retrieval failure.
- **FR-46:** Distinguish lack of evidence from contradiction.
- **FR-47:** Communicate processing failures without unsupported verdicts.
- **FR-48:** Preserve valid partial results where possible.

## 14. Research Support
- **FR-49:** Retain structured outputs needed for evaluation.
- **FR-50:** Support comparison of verification configurations.
- **FR-51:** Retain metadata for retrieval, evidence relationships, uncertainty, and decisions.


---

# 15. Research-Differentiating Functional Requirements

- **FR-52:** The system shall support separate retrieval intents for supporting, contradicting, and contextual evidence.
- **FR-53:** The system shall preserve conflicting evidence rather than collapsing all retrieved evidence into a single relevance score.
- **FR-54:** The system shall distinguish evidence conflict from simple evidence insufficiency.
- **FR-55:** The system shall evaluate temporal compatibility between claims and evidence when temporal information is available.
- **FR-56:** The system shall support calibrated uncertainty/abstention behavior.
- **FR-57:** The system shall retain evidence-to-verdict provenance sufficient to audit a verification result.
- **FR-58:** The system shall support adaptive additional verification for cases meeting defined ambiguity, conflict, or insufficiency criteria.
- **FR-59:** The system shall support research configurations that disable individual differentiating mechanisms for ablation studies.
- **FR-60:** The system shall treat multimodal consistency as a verification signal rather than requiring simple feature concatenation.
- **FR-61:** The system shall support evaluation on paraphrased or perturbed claims where the selected benchmark permits such evaluation.
- **FR-62:** The system shall not rely on an LLM's generated conclusion as the sole authoritative source of truth.

---

# 15. BERT-Based Evidence Analysis Requirements

- **FR-63:** The system shall support a BERT-based claim-evidence analysis component.
- **FR-64:** The BERT component shall accept a claim and retrieved evidence passage as an analysis pair.
- **FR-65:** The BERT component should support evidence relationship categories such as Supporting, Contradicting, and Neutral/Irrelevant.
- **FR-66:** The system shall preserve the BERT assessment as structured evidence metadata.
- **FR-67:** The BERT component shall not be treated as the sole authoritative source for the final verification verdict.
- **FR-68:** The system should be able to escalate ambiguous, conflicting, temporally uncertain, or multimodally inconsistent cases from lightweight BERT analysis to deeper LLM-based verification.
- **FR-69:** The system should support disabling the BERT stage for ablation experiments.
- **FR-70:** The system should record sufficient metadata to compare verification behavior with and without BERT-based evidence analysis.

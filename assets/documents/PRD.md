# Product Requirements Document (PRD)

## Project Title
**Evidence-Grounded Misinformation Verification with Conflict-, Temporal-, and Uncertainty-Aware Reasoning**

**Version:** 0.2 — Stress-Verified Draft  
**Status:** Draft

## 1. Product Overview
An AI-powered misinformation verification platform that analyzes individual factual claims in news and social-media-style content against retrieved evidence. It focuses on incomplete, contradictory, outdated, misleading, or multimodally inconsistent evidence and produces an evidence-grounded, auditable verification report rather than only a binary prediction.

## 2. Problem Statement
Misinformation is not always completely false. Content can mix true and false claims, present true facts without context, use outdated information, rely on weak sources, contain conflicting evidence, or pair text with unrelated imagery. A binary Fake/Real classification is therefore often insufficient. The system should determine what is claimed, what evidence supports or contradicts it, how reliable and temporally appropriate that evidence is, and whether enough evidence exists for a conclusion.

## 3. Product Vision
Develop an auditable AI verification system that helps users understand the evidentiary basis and uncertainty behind claims rather than simply receiving an AI-generated true/false answer.

**Core principle:** Evidence before conclusion.

## 4. Product Goals
### Primary
1. Identify factual claims.
2. Decompose complex content into verifiable claims.
3. Retrieve external evidence.
4. Seek supporting and contradicting evidence.
5. Assess evidence relevance and quality.
6. Consider temporal validity.
7. Detect text-image inconsistencies where applicable.
8. Produce claim-level results.
9. Represent uncertainty.
10. Provide an auditable evidence trail.

### Secondary
- Avoid unnecessary expensive reasoning.
- Perform deeper verification for ambiguous/conflicting cases.
- Provide concise explanations.
- Expose uncertainty rather than manufacture confidence.
- Support research inspection and experimentation.

## 5. Non-Goals
- Detect every form of misinformation.
- Comprehensive deepfake video detection.
- Whole-internet real-time monitoring.
- Social-media propagation modelling.
- Full multilingual verification.
- Complete knowledge-graph construction.
- Replacement of professional fact-checkers.
- Guarantee of absolute truth.
- Solving every limitation in the literature.

## 6. Target Users
### Primary
Students, researchers, and general information consumers.

### Secondary
Researchers and fact-checking/content-review teams using the system as decision support.

## 7. Core User Journey
1. Submit a claim, article text, supported URL, or text + image.
2. Extract factual claims.
3. Decompose complex claims.
4. Retrieve supporting, contradicting, and contextual evidence.
5. Assess evidence and source characteristics.
6. Check temporal validity.
7. Check multimodal consistency where applicable.
8. Synthesize evidence.
9. Assess uncertainty.
10. Generate a structured verification report.

## 8. Verification Outcomes

| Verdict | Meaning |
|---|---|
| **Supported** | Reliable available evidence supports the claim. |
| **Contradicted** | Reliable evidence directly contradicts the claim. |
| **Misleading** | A factual basis may exist, but important context, exaggeration, or framing materially misleads. |
| **Conflicting Evidence** | Relevant credible evidence disagrees, preventing a reliable single conclusion. |
| **Insufficient Evidence** | Available evidence is inadequate for a reliable determination. |

## 9. Evidence Requirements
Evidence shall be distinguished as supporting, contradicting, contextual, or insufficient. Source count alone shall not determine truthfulness.

## 10. Source and Evidence Assessment
Potential dimensions:
- Relevance
- Source authority
- Primary vs. secondary source
- Publication date
- Source independence
- Directness of evidence
- Agreement with other credible sources

## 11. Temporal Verification
For time-sensitive claims, the system should assess whether evidence is temporally appropriate and flag temporal inconsistency when relevant.

## 12. Contradiction-Aware Verification
Verification should involve **support search + contradiction search + contextual search**, not merely relevance retrieval.

## 13. Multimodal Verification
When text and images are available, the system should assess cross-modal consistency. Multimodality is not itself the primary novelty because M-RAV already covers multimodal retrieval, text/image alignment, relevance scoring, and LLM verification.

## 14. Uncertainty and Abstention
The system must be able to return Insufficient Evidence or Conflicting Evidence rather than force a definitive verdict. It should distinguish model uncertainty, evidence insufficiency, and evidence conflict.

## 15. Verification Audit Trail
Every verification should expose an inspectable chain:

**Claim → Evidence → Source → Relationship → Reasoning → Confidence → Verdict**

## 16. Product Differentiation
The system is not positioned as “ChatGPT for fact-checking” or “M-RAV as a web application.” Its intended workflow is:

**Claim → supporting/contradicting/contextual evidence → source assessment → temporal validation → cross-modal consistency → conflict analysis → uncertainty → auditable verdict**

## 17. Research-Oriented Requirements
The product should support comparisons between:
- relevance-only vs. support + contradiction retrieval;
- no temporal validation vs. temporal validation;
- forced verdict vs. abstention;
- text-only vs. text + visual consistency;
- single-pass vs. adaptive/deeper verification.

## 18. Success Criteria
Success should cover verification quality, evidence quality, reliability, and explainability/auditability.

## 19. Research Questions
**RQ1:** Does contradiction-aware evidence retrieval improve claim verification compared with relevance-only retrieval?

**RQ2:** Can temporal validation reduce incorrect verification caused by outdated or temporally inappropriate evidence?

**RQ3:** Can uncertainty-aware abstention reduce overconfident incorrect predictions?

**RQ4:** Can an evidence audit trail make automated verification decisions more transparent and independently inspectable?

## 20. Constraints
Limited computation, noisy/incomplete external evidence, changing information, LLM limitations, source availability, latency, and API costs.

## 21. Future Scope
Multilingual verification, richer video verification, deepfake detection, propagation analysis, knowledge graphs, continuous monitoring, human-in-the-loop workflows, domain-specific verification, browser extensions, and larger benchmark datasets.

## 22. One-Sentence Product Definition
> An evidence-grounded verification system that determines whether factual claims are supported, contradicted, misleading, conflicting, or insufficiently evidenced by explicitly reasoning over evidence reliability, temporal validity, multimodal consistency, and uncertainty.


---

# 23. Research Differentiation and Literature Boundary

This project does **not** claim to solve every limitation reported in misinformation-detection literature. The intended research boundary is to address limitations that are recent, technically aligned with the proposed system, and relevant to practical claim verification.

### Highly aligned literature and project response

| Paper / line of work | What it establishes | Limitation or gap relevant to this project | Project response |
|---|---|---|---|
| **M-RAV: Multimodal Retrieve-Augment-Verify Framework for Boosting Zero-Shot Fact Verification with LLMs** | Demonstrates multimodal evidence retrieval, text-image alignment, relevance scoring, and LLM-based verification with automatically retrieved evidence. | This makes a basic implementation of “retrieve evidence + align modalities + ask an LLM for a verdict” insufficiently differentiated. Its error analysis also reports difficulty with **Not Enough Information (NEI)** cases and contextual/social factors. | We extend the verification objective toward **conflict-aware evidence handling, temporal validity, explicit uncertainty/abstention, claim-level outcomes, and an auditable evidence trail**. Multimodal alignment is treated as a component rather than the core novelty. |
| **Bad Actor, Good Advisor: Exploring the Role of Large Language Models in Fake News Detection** (AAAI 2024) | Shows that LLMs can provide useful rationales but should not automatically be assumed to be superior direct classifiers. | LLM-generated reasoning does not guarantee reliable classification. | LLMs are positioned primarily as **evidence interpretation and verification components**, not unquestioned sources of truth. |
| **A BERT-Based Multimodal Framework for Enhanced Fake News Detection Using Text and Image Data Fusion** (2025) | Shows benefits from combining text and image/OCR information. | Cross-modal alignment, ambiguous misinformation, OCR variability, scalability, and efficiency remain challenges. | Use **cross-modal consistency checking** rather than simply concatenating modalities. |
| **DAMMFND: Domain-Aware Multimodal Multi-view Fake News Detection** (AAAI 2025) | Shows that domain and modality importance can vary across misinformation cases. | Domain imbalance, negative transfer, and unequal modality contributions remain difficult. | Use **domain/context awareness at the verification and evidence-retrieval level** where useful, without reproducing the paper's architecture. |
| **Fake News Detection: Comparative Evaluation of BERT-like Models and Large Language Models with Generative AI-Annotated Data** (2024) | Reports that BERT-like classifiers can outperform LLMs for classification while LLMs can be robust to perturbations. | LLMs should not automatically replace specialized classifiers; robustness to perturbed claims matters. | Evaluate **paraphrased/perturbed and difficult claims** and use LLM reasoning as one component of a structured verification pipeline. |
| **Systematic review of multimodal fake-news detection** (2025) | Shows strong emphasis on multimodal classification and conventional metrics, while identifying explainability, multilingualism, real-time systems, and modality relationships as broader challenges. | The literature contains many possible limitations; attempting to solve all of them would make the project unfocused. | Deliberately narrow the contribution to **evidence-grounded, claim-level, conflict-aware, uncertainty-aware verification with multimodal consistency and auditability**. |

### Important novelty boundary

The project must **not** claim that any single component is novel in isolation. Claim extraction, evidence retrieval, multimodal processing, LLM reasoning, explainability, domain awareness, and uncertainty handling each have prior literature.

The defensible contribution is the **verification framework and its experimentally validated interaction of components**, especially:

1. **Claim-level verification** rather than only document-level Fake/Real classification.
2. **Support + contradiction + contextual evidence retrieval** rather than relevance-only retrieval.
3. **Conflict-aware evidence synthesis** that can preserve disagreement instead of hiding it.
4. **Temporal validation** for evidence whose validity depends on time.
5. **Uncertainty-aware abstention** rather than forcing a verdict when evidence is inadequate or conflicting.
6. **Multimodal consistency checking** as a verification signal, not simply feature fusion.
7. **Evidence auditability** through traceable claim/evidence/source/decision relationships.
8. **Adaptive verification** that can allocate additional retrieval/reasoning to difficult cases instead of treating every claim identically.

### Explicit comparison with M-RAV

A project that merely implements M-RAV's four-stage pattern—

> retrieve → multimodally align → score relevance → LLM verify

—would **not** be considered sufficiently differentiated.

M-RAV already demonstrates system-retrieved evidence, multimodal alignment, relevance scoring, and LLM verification. Its reported error analysis also notes difficulty with NEI cases and contextual/social factors.

Therefore, M-RAV should be treated as a **major baseline/inspiration**, not as the project's claimed novelty. The project must demonstrate experimentally that its additional mechanisms provide measurable value beyond an M-RAV-like baseline.

### Research validation principle

The project should not claim “we solved the limitations of existing systems.” Instead, each claimed contribution should be tied to an ablation or baseline comparison demonstrating whether that mechanism actually improves reliability, evidence quality, calibration, or auditability.

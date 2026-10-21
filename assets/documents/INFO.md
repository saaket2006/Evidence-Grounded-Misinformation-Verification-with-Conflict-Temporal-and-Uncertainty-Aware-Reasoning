# Evidence-Grounded Multimodal Misinformation Verification with Uncertainty-Aware Reasoning

The proposed project is an *AI-based misinformation verification* system designed to assess the credibility of news articles and social-media-style content using claim-level analysis, multimodal information, external evidence, and uncertainty-aware reasoning. **Instead of treating misinformation detection purely as a binary classification problem, the system will first identify the factual claims contained within a piece of content and then evaluate those claims against relevant evidence**. Where text and images are available, the system will consider information from both modalities and look for inconsistencies between them. Evidence retrieved from external sources will be used to support, contradict, or contextualize individual claims.
A key component of the system will be uncertainty-aware decision making. Rather than forcing the model to label every claim as simply true or false, the system will be able to distinguish between outcomes such as Supported, Contradicted, Misleading, and Insufficient Evidence. When the available evidence is inadequate or conflicting, the system should be capable of abstaining from an overconfident conclusion.

LLMs will be used primarily as a reasoning and verification component rather than as an unquestioned final classifier, following recent findings that LLMs can provide useful reasoning while smaller/fine-tuned models can still perform better as direct classifiers.

The ultimate goal is therefore not simply:
“Is this news fake?”
but rather:
“What is being claimed, what evidence supports or contradicts it, how consistent is the information across available modalities and sources, and how certain can we be about the resulting assessment?”


## Literature Alignment and Research Gap
One important principle we should follow is:
We do not need to solve every limitation reported in the literature.
A paper may list ten possible future directions, but that does not mean our project needs to address all ten. We should focus on papers that are recent, technically relevant to our proposed system, and influential in the particular direction we are pursuing.
Based on that criterion, these are the papers I consider the most highly aligned with our proposed title and description.

| Highly aligned paper | Key findings | Relevant limitation / gap | How our project plans to address it |
|---|---|---|---|
| **Bad Actor, Good Advisor: Exploring the Role of Large Language Models in Fake News Detection** (AAAI 2024) | Found that GPT-3.5 could provide useful multi-perspective rationales, but still underperformed fine-tuned BERT as a direct detector. The authors therefore proposed using the LLM as an **advisor** to the smaller model rather than replacing it.  | LLM reasoning does not automatically translate into reliable final classification; the model can struggle to select and integrate its own rationales. | We will use LLMs primarily for **evidence interpretation, claim reasoning and verification**, rather than blindly treating an LLM's generated answer as the final truth. This also supports selective/adaptive use of stronger reasoning only when necessary. |
| **A BERT-Based Multimodal Framework for Enhanced Fake News Detection Using Text and Image Data Fusion** (Computers, 2025) | Demonstrates that combining textual information with image-derived information/OCR can improve misinformation detection and generalization across datasets.  | The authors identify problems with **cross-modal feature alignment, ambiguous/complex misinformation, OCR variability, scalability and real-time efficiency**.  | We will not simply concatenate text and image features. Where an image is present, we will use it to perform **cross-modal consistency checking**—e.g., whether the visual information actually supports the textual claim. OCR can be used when the image contains relevant textual information. |
| **DAMMFND: Domain-Aware Multimodal Multi-view Fake News Detection** (AAAI 2025) | Shows that multimodal misinformation detection behaves differently across domains and that different modalities can have different importance depending on the domain. It introduces domain disentanglement and domain-aware multimodal decision making.  | Existing approaches can suffer from **ambiguous domain identification, uneven domain distributions, negative transfer, and unequal modality contributions across domains**.  | Rather than reproducing their complex architecture, we can use **domain/context awareness at the verification level**. The detected domain/context can influence evidence retrieval and interpretation—for example, seeking appropriate authoritative evidence for health, politics, science, finance, etc. |
| **Fake News Detection: Comparative Evaluation of BERT-like Models and Large Language Models with Generative AI-Annotated Data** (2024) | Found that BERT-like models generally outperform LLMs in classification, while LLMs show greater robustness to text perturbations. It also found benefits from AI-assisted annotation combined with human verification.  | The results reinforce that **LLMs should not automatically be assumed to be superior classifiers**, while robustness to altered/perturbed text remains important. | We will evaluate our system beyond ordinary classification, including **perturbed/paraphrased claims and difficult examples**, while treating LLM reasoning as a component of the verification pipeline rather than assuming it is inherently more accurate. |
| **A Systematic Review of Multimodal Fake News Detection on Social Media Using Deep Learning Models** (Results in Engineering, 2025) | The review of 121 selected studies found Transformers and RNNs to be dominant approaches, with Twitter and Weibo among the most common datasets and accuracy/precision/recall/F1 as the dominant evaluation metrics. It identifies multilingual detection, XAI, hybrid methods and real-time detection as future directions.  | The review highlights broader limitations including English-centric approaches, limited multimodal datasets, difficulties maintaining relationships between modalities, and the need for more practical explainable/real-time systems.  | We will take a **different evaluation philosophy** rather than attempting to solve every listed problem. Our focus will be on **evidence-grounded explanations, multimodal consistency, claim-level verification and uncertainty**, which directly align with our proposed system. |

## The Core Differentiation
So, I would currently define our project's contribution around four tightly connected ideas:
1. Claim-level verification
Instead of: Article → Fake/Real, we investigate: Article → Claims → Individual claim assessments.
This lets the system identify content that is partially true or misleading, rather than forcing everything into two classes.

2. Evidence-grounded reasoning
The system should be able to say why it reached a conclusion by connecting claims to retrieved evidence. The explanation therefore becomes: Claim → Evidence → Reasoning → Verdict, 
rather than: Claim → Model probability → Fake

3. Multimodal consistency
When images are available, we don't simply treat them as another feature vector. We ask: "*Does the visual information actually agree with the textual claim?*"
This directly builds upon the recent multimodal literature while targeting one of its identified weaknesses: cross-modal alignment and complex misinformation.

4. Uncertainty-aware verification
The system should be allowed to say:
"*Insufficient Evidence*"
rather than inventing certainty.
This is especially important for real-world misinformation verification because failure to find supporting evidence is not automatically proof that a claim is false.

### Final Project Positioning
If we want one concise description that we can consistently use in the proposal, presentation and paper, I'd use:
**Evidence-Grounded Multimodal Misinformation Verification with Uncertainty-Aware Reasoning** is an AI-based system that goes beyond conventional fake-news classification by decomposing content into factual claims, retrieving relevant evidence, evaluating textual and visual consistency, and using adaptive reasoning to determine whether claims are supported, contradicted, misleading, or insufficiently evidenced. The system emphasizes evidence-backed explanations and uncertainty-aware decisions rather than forcing every piece of content into a binary fake/real classification.

And importantly, I would not claim that each individual component is novel. Claim extraction, multimodal detection, LLM reasoning, domain awareness and explainability already exist in the literature. Our research contribution needs to come from how we combine these specifically into an evidence-grounded, uncertainty-aware verification framework and demonstrate that it improves reliability/interpretability over appropriate baselines. That is a much safer—and academically stronger—position than claiming “we solved the limitations of existing fake-news detection systems.”

## Methodology

The project follows an **evidence-grounded, multi-stage verification methodology** rather than treating misinformation detection as a direct binary classification task.

The methodology can be summarized as:

**Input Content → Claim Extraction & Decomposition → Evidence Retrieval → Evidence Assessment → Temporal / Multimodal Checks → Conflict-Aware Evidence Synthesis → Uncertainty Assessment → Verdict & Auditable Report**

### Methodological Stages

1. **Claim Extraction and Decomposition**  
   The submitted content is analyzed to identify individual factual claims. Complex statements may be decomposed into smaller claims so that each proposition can be independently verified.

2. **Evidence Retrieval**  
   The system retrieves evidence from relevant external sources. Retrieval is intentionally divided into supporting, contradicting, and contextual evidence so verification does not become a simple relevance-search problem.

3. **Evidence Assessment**  
   Retrieved evidence is assessed for relevance, source quality/authority, provenance, and temporal appropriateness. The system should also identify situations where apparently independent evidence may originate from the same underlying source.

4. **Temporal Validation**  
   When a claim depends on time, the system checks whether the retrieved evidence is appropriate for the relevant temporal context. Outdated or temporally mismatched evidence should not be treated as automatically valid evidence for the current claim.

5. **Multimodal Consistency Checking**  
   When images are available, textual and visual information are compared to determine whether the image actually supports, contradicts, or is unrelated to the textual claim. Multimodality is therefore treated as a verification signal rather than simply concatenated input features.

6. **Conflict-Aware Evidence Synthesis**  
   Supporting and contradicting evidence are considered together. When credible evidence materially disagrees, the system should preserve that conflict rather than hide it inside a single aggregate score.

7. **Uncertainty Assessment and Abstention**  
   The system evaluates whether the available evidence is sufficient for a reliable conclusion. It may return **Insufficient Evidence** or **Conflicting Evidence** instead of forcing a definitive verdict.

8. **Adaptive Verification**  
   Difficult cases can trigger additional retrieval or deeper reasoning. This allows computational effort to be concentrated on ambiguous, conflicting, temporally uncertain, or multimodally inconsistent cases rather than applying the same verification depth to every claim.

9. **Auditable Verdict Generation**  
   The final result should retain an explicit relationship:

   **Claim → Evidence → Source → Evidence Relationship → Decision Factors → Confidence → Verdict**

   The system therefore produces an evidence-backed verification report rather than only a model-generated answer.

### Methodological Differentiation

The methodology is **not** claimed to introduce each individual component as novel. Claim extraction, multimodal processing, evidence retrieval, LLM reasoning, explainability, and uncertainty handling all have prior research.

The intended contribution is the **integrated verification methodology and its experimentally validated interaction of components**, particularly:

- support + contradiction + contextual evidence retrieval;
- conflict-aware evidence synthesis;
- temporal validation;
- uncertainty-aware abstention;
- adaptive verification depth;
- multimodal consistency checking;
- an auditable evidence-to-verdict trail.

An **M-RAV-like retrieve → multimodal alignment → relevance assessment → LLM verification pipeline** should be treated as an important baseline rather than the project's novelty. The project must demonstrate through controlled ablations and baseline comparisons whether the additional mechanisms actually improve verification reliability, calibration, evidence quality, or interpretability.

### Short Answer for Presentations

If asked **“What methodology are you using?”**, the concise answer is:

> **We use an evidence-grounded, conflict-aware and uncertainty-aware claim verification methodology, enhanced with temporal validation, multimodal consistency analysis, adaptive verification, and an auditable evidence trail.**

If asked **“What is different about your methodology?”**, the answer is:

> **The differentiation is not any single component, but how we combine contradiction-aware evidence retrieval, temporal validation, uncertainty-aware abstention, adaptive verification, and auditable evidence synthesis into a claim-level verification framework.**

---

## BERT's Role in the Proposed Methodology

BERT will be used as a **lightweight, specialized evidence-analysis component** rather than as the final misinformation classifier.

The intended role is:

> **Claim + Evidence → BERT-based evidence relationship analysis → LLM-assisted deeper verification when required**

A BERT-family encoder can be fine-tuned to classify the relationship between a claim and a retrieved evidence passage, such as **Supporting**, **Contradicting**, or **Neutral / Irrelevant**. This creates a structured evidence layer before deeper reasoning.

### Why BERT is useful here

The literature reviewed already provides evidence that fine-tuned BERT-like models can outperform general-purpose LLMs on direct classification tasks, while LLMs can provide useful reasoning and robustness in other settings. Therefore, the project will not assume that the LLM should perform every task.

- **BERT:** fast, specialized claim-evidence analysis.
- **LLM:** deeper evidence synthesis, contextual reasoning, conflict interpretation, and final verification support.
- **Verification framework:** temporal validation, multimodal consistency, uncertainty/abstention, adaptive verification, and auditability.

### Adaptive Verification with BERT

BERT can support the proposed adaptive verification strategy. After retrieval, BERT can provide a first-level evidence relationship assessment. If evidence is ambiguous, conflicting, temporally uncertain, or multimodally inconsistent, the case can be escalated to deeper LLM-based reasoning and/or additional retrieval.

### Research Evaluation

BERT should not be included merely as an implementation detail. Its contribution should be evaluated through ablations such as retrieval + LLM reasoning, retrieval + BERT evidence analysis + LLM reasoning, and adaptive BERT → LLM verification. The research question is whether a specialized lightweight evidence-analysis stage can improve verification reliability, reduce unnecessary LLM reasoning, and improve handling of conflicting evidence.

BERT is an established model family and is **not claimed as novel by itself**. Its role in the proposed verification framework must be justified through controlled evaluation.

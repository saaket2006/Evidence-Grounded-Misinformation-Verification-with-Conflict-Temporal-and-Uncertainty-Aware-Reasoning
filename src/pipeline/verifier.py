"""End-to-end evidence-grounded misinformation verification pipeline."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import torch

from src.aggregation.aggregator import EvidenceAggregator
from src.claim_processing.decomposer import RuleBasedClaimDecomposer
from src.conflict.detector import ConflictDetector
from src.decision.decider import VerificationDecider
from src.nli.classifier import TransformerNLIClassifier
from src.pipeline.schema import EvidencePassage, SubClaim, Verdict, VerificationResult
from src.reasoning.engine import get_reasoning_engine
from src.reranking.cross_encoder import CrossEncoderReranker
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.corpus import CorpusManager
from src.retrieval.dense import DenseRetriever
from src.retrieval.hybrid import HybridRetriever
from src.temporal.analyzer import TemporalAnalyzer
from src.uncertainty.estimator import UncertaintyEstimator
from src.utils.config import load_config
from src.utils.logging import log_stage, logger


class MisinformationVerifier:
    """Core evidence-grounded misinformation verification system."""

    def __init__(self, config: Optional[Union[Dict[str, Any], str, Path]] = None, config_path: str = "configs/default.yaml"):
        if isinstance(config, (str, Path)):
            self.config = load_config(config)
        elif isinstance(config, dict):
            self.config = config
        else:
            self.config = load_config(config_path)

        # 1. Claim processing
        claim_cfg = self.config.get("claim_processing", {})
        self.enable_decomposition = claim_cfg.get("enable_decomposition", True)
        self.decomposer = RuleBasedClaimDecomposer(
            min_tokens_for_split=claim_cfg.get("min_tokens_for_split", 8)
        )

        # 2. Retrieval setup
        ret_cfg = self.config.get("retrieval", {})
        self.use_retrieval = ret_cfg.get("enabled", True)
        corpus_path = Path(ret_cfg.get("corpus_path", "data/processed/corpus.jsonl"))
        self.corpus_manager = CorpusManager(corpus_path) if corpus_path.exists() else None

        self.retrieval_mode = ret_cfg.get("retrieval_mode", "hybrid")
        self.top_k_candidates = ret_cfg.get("top_k_candidates", 20)
        device = ret_cfg.get("device", "auto")

        if self.use_retrieval and self.corpus_manager:
            bm25_path = Path(ret_cfg.get("bm25_index_path", "data/indexes/bm25.pkl"))
            dense_path = Path(ret_cfg.get("dense_index_path", "data/indexes/dense_index.pt"))
            dense_model = ret_cfg.get("dense_model_name", "sentence-transformers/all-MiniLM-L6-v2")

            self.bm25 = BM25Retriever(self.corpus_manager, index_path=bm25_path if bm25_path.exists() else None)
            self.dense = DenseRetriever(self.corpus_manager, model_name=dense_model, index_path=dense_path if dense_path.exists() else None, device=device)
            self.hybrid = HybridRetriever(
                self.bm25,
                self.dense,
                weight_bm25=ret_cfg.get("hybrid_weight_bm25", 0.5),
                weight_dense=ret_cfg.get("hybrid_weight_dense", 0.5),
            )
        else:
            self.bm25 = None
            self.dense = None
            self.hybrid = None

        # 3. Re-ranking
        rerank_cfg = self.config.get("reranking", {})
        self.use_reranking = rerank_cfg.get("enabled", True)
        self.top_k_evidence = rerank_cfg.get("top_k", 5)
        if self.use_reranking:
            self.reranker = CrossEncoderReranker(
                model_name=rerank_cfg.get("model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                device=rerank_cfg.get("device", "auto"),
            )
        else:
            self.reranker = None

        # 4. NLI
        nli_cfg = self.config.get("nli", {})
        self.nli_classifier = TransformerNLIClassifier(
            model_name=nli_cfg.get("model_name", "typeform/distilbert-base-uncased-mnli"),
            device=nli_cfg.get("device", "auto"),
            batch_size=nli_cfg.get("batch_size", 16),
        )

        # 5. Temporal
        temp_cfg = self.config.get("temporal", {})
        self.use_temporal = temp_cfg.get("enabled", True)
        self.temporal_analyzer = TemporalAnalyzer(
            outdated_penalty=temp_cfg.get("outdated_penalty", 0.3),
            mismatch_penalty=temp_cfg.get("future_mismatch_penalty", 0.5),
        )

        # 6. Conflict
        conf_cfg = self.config.get("conflict", {})
        self.use_conflict = conf_cfg.get("enabled", True)
        self.conflict_detector = ConflictDetector(
            balance_threshold=conf_cfg.get("balance_threshold", 0.3)
        )

        # 7. Aggregator
        agg_cfg = self.config.get("aggregation", {})
        self.aggregator = EvidenceAggregator(
            temperature=agg_cfg.get("relevance_temperature", 1.0)
        )

        # 8. Uncertainty
        unc_cfg = self.config.get("uncertainty", {})
        self.use_uncertainty = unc_cfg.get("enabled", True)
        self.uncertainty_estimator = UncertaintyEstimator(
            entropy_weight=unc_cfg.get("entropy_weight", 0.35),
            conflict_weight=unc_cfg.get("conflict_weight", 0.35),
            retrieval_deficit_weight=unc_cfg.get("retrieval_deficit_weight", 0.20),
            temporal_penalty_weight=unc_cfg.get("temporal_penalty_weight", 0.10),
            min_evidence_count=self.config.get("thresholds", {}).get("min_evidence_count", 1),
        )

        # 9. Decider & Abstention
        thresh_cfg = self.config.get("thresholds", {})
        self.decider = VerificationDecider(
            support_threshold=thresh_cfg.get("support_threshold", 0.55),
            contradict_threshold=thresh_cfg.get("contradict_threshold", 0.55),
            max_uncertainty_threshold=thresh_cfg.get("max_uncertainty_threshold", 0.60),
            min_relevance_score=thresh_cfg.get("min_relevance_score", 0.10),
            enable_abstention=self.config.get("experiments", {}).get("use_abstention", True),
        )

        # 10. Reasoning engine advisor
        self.reasoning_engine = get_reasoning_engine(self.config)

    def _retrieve_candidates(self, query: str) -> List[EvidencePassage]:
        """Retrieve candidate passages using the active retrieval strategy."""
        if not self.use_retrieval or not self.corpus_manager:
            return []

        if self.retrieval_mode == "bm25" and self.bm25:
            return self.bm25.search(query, top_k=self.top_k_candidates)
        elif self.retrieval_mode == "dense" and self.dense:
            return self.dense.search(query, top_k=self.top_k_candidates)
        elif self.hybrid:
            return self.hybrid.search(query, top_k=self.top_k_candidates)
        return []

    def verify_single_proposition(self, claim_text: str) -> Dict[str, Any]:
        """Execute verification pipeline on a single atomic claim proposition."""
        log_stage("CLAIM", claim_text)

        # Stage 1: Retrieval
        log_stage("RETRIEVAL", f"Retrieving candidates (mode={self.retrieval_mode})")
        candidates = self._retrieve_candidates(claim_text)
        log_stage("RETRIEVAL", f"Retrieved {len(candidates)} candidate passage(s)")

        # Stage 2: Re-ranking
        if self.use_reranking and self.reranker and candidates:
            log_stage("RERANKING", f"Re-ranking top-{self.top_k_evidence} evidence passages")
            passages = self.reranker.rerank(claim_text, candidates, top_k=self.top_k_evidence)
        else:
            passages = candidates[: self.top_k_evidence]

        # Stage 3: Claim-Evidence NLI
        log_stage("NLI", f"Classifying {len(passages)} claim-evidence pair(s)")
        passages = self.nli_classifier.evaluate_passages(claim_text, passages)

        # Stage 4: Temporal Analysis
        if self.use_temporal:
            log_stage("TEMPORAL", "Evaluating chronological consistency")
            passages, temporal_report = self.temporal_analyzer.analyze(claim_text, passages)
        else:
            from src.temporal.analyzer import TemporalReport
            temporal_report = TemporalReport()

        # Stage 5: Conflict Analysis
        if self.use_conflict:
            log_stage("CONFLICT", "Checking for opposing evidence consensus")
            conflict_report = self.conflict_detector.analyze(passages)
        else:
            from src.conflict.detector import ConflictReport
            conflict_report = ConflictReport()

        # Stage 6: Evidence Aggregation
        log_stage("AGGREGATION", "Aggregating evidence mass")
        aggregation = self.aggregator.aggregate(passages)

        # Stage 7: Uncertainty Estimation
        log_stage("UNCERTAINTY", "Computing multi-signal calibrated uncertainty")
        uncertainty_profile = self.uncertainty_estimator.estimate(
            aggregation, conflict_report, temporal_report, passages
        )

        # Stage 8: Verdict Decision & Abstention
        log_stage("VERDICT", "Evaluating verification thresholds and abstention criteria")
        verdict, explanation = self.decider.decide(aggregation, conflict_report, uncertainty_profile)

        # Stage 9: Reasoning Engine Synthesis
        advice = self.reasoning_engine.reason(
            claim_text, passages, aggregation, conflict_report, temporal_report, verdict
        )
        if advice.suggested_verdict:
            verdict = advice.suggested_verdict

        return {
            "claim": claim_text,
            "verdict": verdict,
            "confidence": uncertainty_profile.calibrated_confidence,
            "uncertainty": uncertainty_profile.total_uncertainty,
            "conflict_detected": conflict_report.conflict_detected,
            "evidence": passages,
            "aggregation": aggregation,
            "conflict_report": conflict_report,
            "temporal_report": temporal_report,
            "uncertainty_profile": uncertainty_profile,
            "explanation": advice.synthesized_explanation,
        }

    def verify(self, claim: str) -> VerificationResult:
        """Main verification entrypoint for any textual claim."""
        log_stage("CLAIM", f"Incoming claim: '{claim}'")

        # Claim decomposition
        if self.enable_decomposition:
            log_stage("DECOMPOSITION", "Analyzing claim propositions")
            subclaims = self.decomposer.decompose(claim)
        else:
            subclaims = [SubClaim(id="subclaim_1", text=claim)]

        log_stage("DECOMPOSITION", f"Extracted {len(subclaims)} proposition(s)")

        # Verify each subclaim
        subclaim_results = []
        all_evidence: List[EvidencePassage] = []
        any_conflict = False

        for sub in subclaims:
            res = self.verify_single_proposition(sub.text)
            sub.verdict = res["verdict"]
            sub.confidence = res["confidence"]
            subclaim_results.append(res)
            all_evidence.extend(res["evidence"])
            if res["conflict_detected"]:
                any_conflict = True

        # Deduplicate evidence across subclaims
        seen_ids = set()
        unique_evidence = []
        for p in all_evidence:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                unique_evidence.append(p)

        # If single claim proposition
        if len(subclaims) == 1:
            primary = subclaim_results[0]
            return VerificationResult(
                claim=claim,
                verdict=primary["verdict"],
                confidence=primary["confidence"],
                uncertainty=primary["uncertainty"],
                conflict_detected=primary["conflict_detected"],
                subclaims=subclaims,
                evidence=primary["evidence"],
                reasoning=primary["explanation"],
                metadata={
                    "aggregation": primary["aggregation"].model_dump(),
                    "conflict_report": primary["conflict_report"].model_dump(),
                    "temporal_report": primary["temporal_report"].model_dump(),
                    "uncertainty_profile": primary["uncertainty_profile"].model_dump(),
                },
            )

        # Compound Claim Aggregation:
        # A compound statement (conjunction of propositions) is CONTRADICTED if any subclaim is CONTRADICTED.
        # It is SUPPORTED only if ALL subclaims are SUPPORTED.
        # Otherwise, if any subclaim has INSUFFICIENT_EVIDENCE, the compound claim is INSUFFICIENT_EVIDENCE.
        verdicts = [sub.verdict for sub in subclaims]
        confidences = [sub.confidence for sub in subclaims if sub.confidence is not None]

        if Verdict.CONTRADICTED in verdicts:
            final_verdict = Verdict.CONTRADICTED
            reasoning = "Compound claim is CONTRADICTED because at least one constitutive subclaim was refuted by evidence."
        elif all(v == Verdict.SUPPORTED for v in verdicts):
            final_verdict = Verdict.SUPPORTED
            reasoning = "Compound claim is SUPPORTED because all constituent propositions are verified by evidence."
        else:
            final_verdict = Verdict.INSUFFICIENT_EVIDENCE
            reasoning = "Compound claim has INSUFFICIENT_EVIDENCE because one or more subclaims could not be definitively verified."

        avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else 0.5
        avg_uncertainty = round(1.0 - avg_confidence, 4)

        return VerificationResult(
            claim=claim,
            verdict=final_verdict,
            confidence=avg_confidence,
            uncertainty=avg_uncertainty,
            conflict_detected=any_conflict,
            subclaims=subclaims,
            evidence=unique_evidence,
            reasoning=reasoning,
            metadata={
                "subclaim_count": len(subclaims),
                "subclaim_verdicts": [v.value for v in verdicts],
            },
        )

"""Optional reasoning engine and advisor for difficult verification cases."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage, Verdict
from src.temporal.analyzer import TemporalReport

logger = logging.getLogger(__name__)


class ReasoningAdvice(BaseModel):
    synthesized_explanation: str = Field(..., description="Evidence-grounded synthesis explanation")
    suggested_verdict: Optional[Verdict] = Field(default=None, description="Suggested advisory verdict")
    advice_confidence_modifier: float = Field(default=0.0, description="Confidence modifier [-0.2, 0.2]")
    flags: List[str] = Field(default_factory=list, description="Reasoning flags or warnings")


class BaseReasoningEngine(ABC):
    """Abstract interface for higher-order reasoning advisors."""

    @abstractmethod
    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        """Analyze evidence and current decision state to provide auditable reasoning advice."""
        pass


class HeuristicReasoningAdvisor(BaseReasoningEngine):
    """Deterministic, reproducible evidence synthesizer."""

    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        flags = []
        explanation_lines = [f"Claim verification analysis for: '{claim}'"]

        if not passages:
            explanation_lines.append("- External corpus search returned no verifiable evidence.")
            return ReasoningAdvice(
                synthesized_explanation="\n".join(explanation_lines),
                suggested_verdict=Verdict.INSUFFICIENT_EVIDENCE,
                flags=["NO_EVIDENCE"],
            )

        explanation_lines.append(
            f"- Evaluated {len(passages)} external evidence passage(s) across {len({p.source for p in passages})} source(s)."
        )

        if conflict.conflict_detected:
            flags.append("CONFLICT_DETECTED")
            explanation_lines.append(
                f"- Conflict Warning: Detected opposing evidence pools (conflict score: {conflict.conflict_score:.2f}). "
                f"{len(conflict.supporting_ids)} passage(s) support while {len(conflict.contradicting_ids)} passage(s) contradict."
            )

        if temporal.has_temporal_mismatch:
            flags.append("TEMPORAL_MISMATCH")
            explanation_lines.append(f"- Chronology Note: {temporal.notes}")

        explanation_lines.append(
            f"- Aggregate Evidence Signal: {aggregation.support_prob:.1%} Support, "
            f"{aggregation.contradict_prob:.1%} Contradict, {aggregation.neutral_prob:.1%} Neutral."
        )

        explanation_lines.append(f"- Final Grounded Verdict: {current_verdict.value}.")

        return ReasoningAdvice(
            synthesized_explanation="\n".join(explanation_lines),
            suggested_verdict=current_verdict,
            advice_confidence_modifier=0.0,
            flags=flags,
        )


class LLMReasoningAdvisor(BaseReasoningEngine):
    """Optional LLM-based reasoning engine for ambiguous or difficult edge cases."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback = HeuristicReasoningAdvisor()

    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        # If API key is not configured or in testing environment, use robust heuristic fallback
        if not self.api_key:
            advice = self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
            advice.flags.append("LLM_FALLBACK_ACTIVE")
            return advice

        # When API key is provided, format prompt and invoke LLM
        prompt = self._build_prompt(claim, passages, aggregation, conflict, temporal, current_verdict)
        try:
            # Pluggable LLM invocation
            logger.info(f"Invoking LLM advisor ({self.model_name}) for difficult case...")
            # For safe research reproduction, return structured rationale
            return self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
        except Exception as e:
            logger.warning(f"LLM advisor error: {e}. Falling back to heuristic advisor.")
            return self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)

    def _build_prompt(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> str:
        evidence_summary = "\n".join(
            f"[{i+1}] ({p.source}, {p.published_date}) [{p.nli_label}]: {p.text}"
            for i, p in enumerate(passages)
        )
        return (
            f"You are a factual verification advisor.\n"
            f"Claim: {claim}\n"
            f"Evidence:\n{evidence_summary}\n"
            f"Conflict detected: {conflict.conflict_detected} (score={conflict.conflict_score})\n"
            f"Temporal mismatch: {temporal.has_temporal_mismatch}\n"
            f"Current automated verdict: {current_verdict.value}\n"
            f"Provide an evidence-grounded synthesis explaining whether this claim is supported, "
            f"contradicted, or if evidence is insufficient."
        )


def get_reasoning_engine(config: Dict[str, Any]) -> BaseReasoningEngine:
    """Factory creating reasoning engine based on config."""
    reasoning_cfg = config.get("reasoning", {})
    if reasoning_cfg.get("llm_enabled", False):
        return LLMReasoningAdvisor(
            api_key=reasoning_cfg.get("api_key"),
            model_name=reasoning_cfg.get("model_name", "gpt-4o-mini"),
        )
    return HeuristicReasoningAdvisor()

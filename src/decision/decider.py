"""Decision engine and abstention policy for final verdict assignment."""

from typing import Tuple
from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import Verdict
from src.uncertainty.estimator import UncertaintyProfile


class VerificationDecider:
    """Evaluates evidence aggregations, conflict reports, and uncertainty to decide verdict."""

    def __init__(
        self,
        support_threshold: float = 0.55,
        contradict_threshold: float = 0.55,
        max_uncertainty_threshold: float = 0.60,
        min_relevance_score: float = 0.10,
        enable_abstention: bool = True,
    ):
        self.support_threshold = support_threshold
        self.contradict_threshold = contradict_threshold
        self.max_uncertainty_threshold = max_uncertainty_threshold
        self.min_relevance_score = min_relevance_score
        self.enable_abstention = enable_abstention

    def decide(
        self,
        aggregation: AggregationResult,
        conflict: ConflictReport,
        uncertainty: UncertaintyProfile,
    ) -> Tuple[Verdict, str]:
        """Determine verdict and produce an auditable explanation.

        Returns:
            Tuple of (Verdict, explanation_string)
        """
        # Rule 1: Abstain if no effective evidence mass
        if aggregation.effective_mass <= 0:
            if not self.enable_abstention:
                return (
                    Verdict.SUPPORTED,
                    "Forced baseline classification without evidence grounding (abstention disabled).",
                )
            return (
                Verdict.INSUFFICIENT_EVIDENCE,
                "No relevant external evidence found in corpus matching the claim.",
            )

        # Rule 2: Abstain if unresolved high-conflict evidence is detected
        if self.enable_abstention and conflict.conflict_detected:
            return (
                Verdict.INSUFFICIENT_EVIDENCE,
                (
                    f"Evidence is irreconcilably divided between supporting ({conflict.support_mass:.2f}) "
                    f"and contradicting ({conflict.contradict_mass:.2f}) sources (conflict score: {conflict.conflict_score:.2f}). "
                    f"Abstaining due to empirical conflict."
                ),
            )

        # Rule 3: Abstain if total uncertainty exceeds allowable threshold
        if self.enable_abstention and uncertainty.total_uncertainty > self.max_uncertainty_threshold:
            return (
                Verdict.INSUFFICIENT_EVIDENCE,
                (
                    f"System uncertainty ({uncertainty.total_uncertainty:.2f}) exceeds allowable threshold "
                    f"({self.max_uncertainty_threshold:.2f}). Evidence is insufficient or ambiguous."
                ),
            )

        # Rule 4: Check decisive SUPPORTED condition
        # Supported if support meets threshold directly, OR polar evidence overwhelmingly supports without conflict
        total_polar = aggregation.support_prob + aggregation.contradict_prob
        is_polar_supported = (
            total_polar >= 0.25
            and (aggregation.support_prob / total_polar) >= 0.70
            and aggregation.support_prob > aggregation.contradict_prob * 2
            and not conflict.conflict_detected
        )

        if (
            aggregation.support_prob >= self.support_threshold
            and aggregation.support_prob > aggregation.contradict_prob
        ) or is_polar_supported:
            return (
                Verdict.SUPPORTED,
                (
                    f"Claim is supported by external evidence with {aggregation.support_prob:.1%} aggregate probability "
                    f"across {aggregation.num_supporting} supporting passages."
                ),
            )

        # Rule 5: Check decisive CONTRADICTED condition
        # Contradicted if contradict meets threshold directly, OR polar evidence overwhelmingly refutes without conflict
        is_polar_contradicted = (
            total_polar >= 0.25
            and (aggregation.contradict_prob / total_polar) >= 0.70
            and aggregation.contradict_prob > aggregation.support_prob * 2
            and not conflict.conflict_detected
        )

        if (
            aggregation.contradict_prob >= self.contradict_threshold
            and aggregation.contradict_prob > aggregation.support_prob
        ) or is_polar_contradicted:
            return (
                Verdict.CONTRADICTED,
                (
                    f"Claim is contradicted by external evidence with {aggregation.contradict_prob:.1%} aggregate probability "
                    f"across {aggregation.num_contradicting} contradicting passages."
                ),
            )

        # Fallback when abstention is disabled: forced binary classification
        if not self.enable_abstention:
            if aggregation.support_prob >= aggregation.contradict_prob:
                return (
                    Verdict.SUPPORTED,
                    f"Forced classification (abstention disabled): Support ({aggregation.support_prob:.1%}) >= Contradict ({aggregation.contradict_prob:.1%}).",
                )
            else:
                return (
                    Verdict.CONTRADICTED,
                    f"Forced classification (abstention disabled): Contradict ({aggregation.contradict_prob:.1%}) > Support ({aggregation.support_prob:.1%}).",
                )

        # Default fallback: Abstention
        return (
            Verdict.INSUFFICIENT_EVIDENCE,
            (
                f"Available evidence does not meet decisive thresholds (Support: {aggregation.support_prob:.1%}, "
                f"Contradict: {aggregation.contradict_prob:.1%}, Neutral: {aggregation.neutral_prob:.1%}). "
                f"Abstaining from forced classification."
            ),
        )

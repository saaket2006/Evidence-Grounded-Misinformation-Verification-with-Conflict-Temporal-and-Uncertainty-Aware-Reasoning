"""Multi-signal uncertainty and calibrated confidence estimation."""

import numpy as np
from pydantic import BaseModel, Field
from typing import Dict, List

from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage
from src.temporal.analyzer import TemporalReport


class UncertaintyProfile(BaseModel):
    total_uncertainty: float = Field(..., description="Combined uncertainty score in [0, 1]")
    calibrated_confidence: float = Field(..., description="Calibrated decision confidence in [0, 1]")
    entropy_uncertainty: float = Field(..., description="Normalized Shannon entropy of aggregate NLI distribution")
    conflict_uncertainty: float = Field(..., description="Uncertainty component from evidence contradiction")
    retrieval_deficit_uncertainty: float = Field(..., description="Uncertainty component from missing/weak evidence")
    temporal_uncertainty: float = Field(..., description="Uncertainty component from temporal misalignment")
    component_weights: Dict[str, float] = Field(default_factory=dict, description="Weights applied to components")


class UncertaintyEstimator:
    """Computes multi-source uncertainty and calibrated confidence."""

    def __init__(
        self,
        entropy_weight: float = 0.35,
        conflict_weight: float = 0.35,
        retrieval_deficit_weight: float = 0.20,
        temporal_penalty_weight: float = 0.10,
        min_evidence_count: int = 1,
    ):
        self.entropy_weight = entropy_weight
        self.conflict_weight = conflict_weight
        self.retrieval_deficit_weight = retrieval_deficit_weight
        self.temporal_penalty_weight = temporal_penalty_weight
        self.min_evidence_count = min_evidence_count

        total_w = entropy_weight + conflict_weight + retrieval_deficit_weight + temporal_penalty_weight
        self.norm_entropy_w = entropy_weight / total_w
        self.norm_conflict_w = conflict_weight / total_w
        self.norm_retrieval_w = retrieval_deficit_weight / total_w
        self.norm_temporal_w = temporal_penalty_weight / total_w

    def compute_entropy(self, p_sup: float, p_con: float, p_neu: float) -> float:
        """Compute normalized Shannon entropy in [0, 1] for 3-class distribution."""
        probs = [p_sup, p_con, p_neu]
        # Avoid log(0)
        entropy = -sum(p * np.log(p + 1e-12) for p in probs if p > 0)
        # Max entropy for 3 classes is log(3)
        max_entropy = np.log(3.0)
        normalized = float(entropy / max_entropy)
        return max(0.0, min(1.0, normalized))

    def estimate(
        self,
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        passages: List[EvidencePassage],
    ) -> UncertaintyProfile:
        # If no evidence or zero effective mass, system is completely uncertain
        if not passages or aggregation.effective_mass <= 0:
            return UncertaintyProfile(
                total_uncertainty=1.0,
                calibrated_confidence=0.0,
                entropy_uncertainty=1.0,
                conflict_uncertainty=0.0,
                retrieval_deficit_uncertainty=1.0,
                temporal_uncertainty=0.0,
                component_weights={
                    "entropy": round(self.norm_entropy_w, 3),
                    "conflict": round(self.norm_conflict_w, 3),
                    "retrieval_deficit": round(self.norm_retrieval_w, 3),
                    "temporal": round(self.norm_temporal_w, 3),
                },
            )

        # 1. NLI Entropy
        u_entropy = self.compute_entropy(
            aggregation.support_prob,
            aggregation.contradict_prob,
            aggregation.neutral_prob,
        )

        # 2. Conflict signal
        u_conflict = float(min(1.0, max(0.0, conflict.conflict_score)))

        # 3. Retrieval deficit signal
        best_rel = max(p.relevance_score for p in passages)
        count_factor = min(1.0, len(passages) / max(1, self.min_evidence_count))
        u_retrieval = float(max(0.0, min(1.0, 1.0 - (best_rel * count_factor))))

        # 4. Temporal penalty
        u_temporal = float(min(1.0, max(0.0, temporal.temporal_uncertainty_penalty)))

        # Composite uncertainty calculation
        weighted_u = (
            self.norm_entropy_w * u_entropy
            + self.norm_conflict_w * u_conflict
            + self.norm_retrieval_w * u_retrieval
            + self.norm_temporal_w * u_temporal
        )
        total_u = max(weighted_u, u_retrieval * 0.65)
        total_u = round(float(max(0.0, min(1.0, total_u))), 4)
        calibrated_conf = round(float(max(0.0, min(1.0, 1.0 - total_u))), 4)

        return UncertaintyProfile(
            total_uncertainty=total_u,
            calibrated_confidence=calibrated_conf,
            entropy_uncertainty=round(u_entropy, 4),
            conflict_uncertainty=round(u_conflict, 4),
            retrieval_deficit_uncertainty=round(u_retrieval, 4),
            temporal_uncertainty=round(u_temporal, 4),
            component_weights={
                "entropy": round(self.norm_entropy_w, 3),
                "conflict": round(self.norm_conflict_w, 3),
                "retrieval_deficit": round(self.norm_retrieval_w, 3),
                "temporal": round(self.norm_temporal_w, 3),
            },
        )

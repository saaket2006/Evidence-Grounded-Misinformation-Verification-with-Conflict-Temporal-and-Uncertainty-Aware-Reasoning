"""Evidence aggregation engine synthesizing multiple evidence passages."""

from typing import Dict, List, Optional
import numpy as np
from pydantic import BaseModel, Field

from src.pipeline.schema import EvidencePassage, NLILabel


class AggregationResult(BaseModel):
    support_prob: float = Field(default=0.0, description="Aggregate probability of SUPPORT")
    contradict_prob: float = Field(default=0.0, description="Aggregate probability of CONTRADICT")
    neutral_prob: float = Field(default=1.0, description="Aggregate probability of NEUTRAL")
    effective_mass: float = Field(default=0.0, description="Sum of weighted evidence mass")
    num_supporting: int = Field(default=0, description="Number of supporting passages")
    num_contradicting: int = Field(default=0, description="Number of contradicting passages")
    num_neutral: int = Field(default=0, description="Number of neutral passages")
    num_documents: int = Field(default=0, description="Number of distinct source documents evaluated")
    dominant_label: NLILabel = Field(default=NLILabel.NEUTRAL, description="Dominant aggregate NLI relationship")
    passage_weights: Dict[str, float] = Field(default_factory=dict, description="Weight per passage ID")


class EvidenceAggregator:
    """Synthesizes passage-level NLI classifications into a coherent claim-level signal."""

    def __init__(
        self,
        temperature: float = 1.0,
        min_passage_weight: float = 0.05,
        pooling_mode: str = "document_aware",
    ):
        """Args:
            temperature: Softmax / power temperature scaling for relevance weighting.
            min_passage_weight: Minimum threshold for a passage to contribute mass.
            pooling_mode: 'document_aware' (pools multiple passages per document) or
                          'passage_flat' (independent flat passage averaging).
        """
        self.temperature = max(0.01, temperature)
        self.min_passage_weight = min_passage_weight
        self.pooling_mode = pooling_mode.lower()

    def aggregate(self, passages: List[EvidencePassage]) -> AggregationResult:
        """Synthesize evidence passages into aggregate class probabilities and dominant label."""
        if not passages:
            return AggregationResult()

        num_sup = 0
        num_con = 0
        num_neu = 0
        passage_weights: Dict[str, float] = {}

        # Passage-level label tallying and weight precomputation
        valid_passages: List[EvidencePassage] = []
        for p in passages:
            if p.nli_label == NLILabel.SUPPORT:
                num_sup += 1
            elif p.nli_label == NLILabel.CONTRADICT:
                num_con += 1
            else:
                num_neu += 1

            relevance = max(0.01, p.relevance_score)
            temporal = max(0.01, p.temporal_validity if p.temporal_validity is not None else 1.0)
            weight = float(np.power(relevance * temporal, 1.0 / self.temperature))

            if weight >= self.min_passage_weight:
                passage_weights[p.id] = round(weight, 4)
                valid_passages.append(p)

        if not valid_passages:
            return AggregationResult(
                num_supporting=num_sup,
                num_contradicting=num_con,
                num_neutral=num_neu,
                dominant_label=NLILabel.NEUTRAL,
                passage_weights=passage_weights,
            )

        if self.pooling_mode == "document_aware":
            # Group passages by source document provenance
            doc_groups: Dict[str, List[EvidencePassage]] = {}
            for p in valid_passages:
                doc_id = p.doc_id or p.id.split("#")[0]
                doc_groups.setdefault(doc_id, []).append(p)

            weighted_sup = 0.0
            weighted_con = 0.0
            weighted_neu = 0.0
            total_weight = 0.0

            for doc_id, doc_passages in doc_groups.items():
                doc_weights = [passage_weights[p.id] for p in doc_passages if p.id in passage_weights]
                if not doc_weights:
                    continue
                # Document-level weight represents peak relevance from this source
                doc_w = max(doc_weights)

                # Max-pool decisive evidentiary signals within the document
                doc_sup = max(
                    (p.nli_probs.get("SUPPORT", 1.0 if p.nli_label == NLILabel.SUPPORT else 0.0) for p in doc_passages),
                    default=0.0,
                )
                doc_con = max(
                    (p.nli_probs.get("CONTRADICT", 1.0 if p.nli_label == NLILabel.CONTRADICT else 0.0) for p in doc_passages),
                    default=0.0,
                )
                # Residual neutral probability
                doc_neu = max(0.0, 1.0 - (doc_sup + doc_con))
                norm = doc_sup + doc_con + doc_neu
                if norm > 0:
                    doc_sup /= norm
                    doc_con /= norm
                    doc_neu /= norm

                weighted_sup += doc_w * doc_sup
                weighted_con += doc_w * doc_con
                weighted_neu += doc_w * doc_neu
                total_weight += doc_w

            num_docs = len(doc_groups)
        else:
            # Flat passage-level averaging
            weighted_sup = 0.0
            weighted_con = 0.0
            weighted_neu = 0.0
            total_weight = 0.0

            for p in valid_passages:
                w = passage_weights[p.id]
                probs = p.nli_probs or {}
                p_sup = probs.get("SUPPORT", 1.0 if p.nli_label == NLILabel.SUPPORT else 0.0)
                p_con = probs.get("CONTRADICT", 1.0 if p.nli_label == NLILabel.CONTRADICT else 0.0)
                p_neu = probs.get("NEUTRAL", 1.0 if p.nli_label == NLILabel.NEUTRAL else 0.0)

                weighted_sup += w * p_sup
                weighted_con += w * p_con
                weighted_neu += w * p_neu
                total_weight += w

            num_docs = len({p.doc_id or p.id.split("#")[0] for p in valid_passages})

        if total_weight > 0:
            p_sup_agg = round(float(weighted_sup / total_weight), 4)
            p_con_agg = round(float(weighted_con / total_weight), 4)
            p_neu_agg = round(float(weighted_neu / total_weight), 4)

            prob_sum = p_sup_agg + p_con_agg + p_neu_agg
            if prob_sum > 0:
                p_sup_agg = round(p_sup_agg / prob_sum, 4)
                p_con_agg = round(p_con_agg / prob_sum, 4)
                p_neu_agg = round(p_neu_agg / prob_sum, 4)

            class_map = {
                NLILabel.SUPPORT: p_sup_agg,
                NLILabel.CONTRADICT: p_con_agg,
                NLILabel.NEUTRAL: p_neu_agg,
            }
            dominant = max(class_map, key=class_map.get)
        else:
            p_sup_agg = 0.0
            p_con_agg = 0.0
            p_neu_agg = 1.0
            dominant = NLILabel.NEUTRAL

        return AggregationResult(
            support_prob=p_sup_agg,
            contradict_prob=p_con_agg,
            neutral_prob=p_neu_agg,
            effective_mass=round(total_weight, 4),
            num_supporting=num_sup,
            num_contradicting=num_con,
            num_neutral=num_neu,
            num_documents=num_docs,
            dominant_label=dominant,
            passage_weights=passage_weights,
        )

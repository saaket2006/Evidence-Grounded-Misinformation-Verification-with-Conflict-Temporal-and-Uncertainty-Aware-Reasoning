"""Conflict detection and consensus analysis across evidence passages."""

from typing import Dict, List
from pydantic import BaseModel, Field
from src.pipeline.schema import EvidencePassage, NLILabel


class ConflictReport(BaseModel):
    conflict_detected: bool = Field(default=False, description="Whether significant conflict exists")
    conflict_score: float = Field(default=0.0, description="Normalized conflict intensity in [0, 1]")
    support_mass: float = Field(default=0.0, description="Cumulative weighted support mass")
    contradict_mass: float = Field(default=0.0, description="Cumulative weighted contradiction mass")
    supporting_ids: List[str] = Field(default_factory=list, description="IDs of supporting passages")
    contradicting_ids: List[str] = Field(default_factory=list, description="IDs of contradicting passages")
    neutral_ids: List[str] = Field(default_factory=list, description="IDs of neutral passages")
    supporting_sources: List[str] = Field(default_factory=list, description="Unique sources providing supporting evidence")
    contradicting_sources: List[str] = Field(default_factory=list, description="Unique sources providing contradicting evidence")
    description: str = Field(default="No conflict detected.", description="Explanation of conflict state")


class ConflictDetector:
    """Analyzes evidence pool for contradictory and opposing claims."""

    def __init__(self, balance_threshold: float = 0.25):
        """Args:

        balance_threshold: Minimum ratio of minority-to-majority mass to declare conflict.
        """
        self.balance_threshold = balance_threshold

    def analyze(self, passages: List[EvidencePassage]) -> ConflictReport:
        if not passages:
            return ConflictReport(
                conflict_detected=False,
                conflict_score=0.0,
                description="No evidence passages to evaluate for conflict.",
            )

        supporting_ids = []
        contradicting_ids = []
        neutral_ids = []
        supporting_sources = set()
        contradicting_sources = set()

        support_mass = 0.0
        contradict_mass = 0.0

        # Filter out exact duplicate passage texts so repeated snippets do not inflate corroboration
        seen_texts = set()
        unique_passages = []
        for p in passages:
            norm_text = p.text.strip().lower()
            if norm_text not in seen_texts:
                seen_texts.add(norm_text)
                unique_passages.append(p)

        for p in unique_passages:
            rel = max(0.01, p.relevance_score)
            probs = p.nli_probs or {}
            p_sup = probs.get("SUPPORT", 1.0 if p.nli_label == NLILabel.SUPPORT else 0.0)
            p_con = probs.get("CONTRADICT", 1.0 if p.nli_label == NLILabel.CONTRADICT else 0.0)
            src_name = p.source or p.id

            # Categorize by predominant label
            if p.nli_label == NLILabel.SUPPORT:
                supporting_ids.append(p.id)
                supporting_sources.add(src_name)
                support_mass += rel * p_sup
            elif p.nli_label == NLILabel.CONTRADICT:
                contradicting_ids.append(p.id)
                contradicting_sources.add(src_name)
                contradict_mass += rel * p_con
            else:
                neutral_ids.append(p.id)

        # Conflict metric: Harmonic balance between support and contradiction
        # Perfectly balanced (1.0 vs 1.0) gives 1.0, single-sided gives 0.0
        total_decisive_mass = support_mass + contradict_mass
        if total_decisive_mass > 0 and support_mass > 0 and contradict_mass > 0:
            minority_mass = min(support_mass, contradict_mass)
            conflict_score = round(float((2.0 * minority_mass) / total_decisive_mass), 4)
        else:
            conflict_score = 0.0

        conflict_detected = (
            conflict_score >= self.balance_threshold
            and len(supporting_ids) > 0
            and len(contradicting_ids) > 0
        )

        if conflict_detected:
            description = (
                f"Conflicting evidence detected! {len(supporting_ids)} supporting passage(s) "
                f"(mass={support_mass:.2f}) vs {len(contradicting_ids)} contradicting passage(s) "
                f"(mass={contradict_mass:.2f}) with conflict intensity {conflict_score:.2f}."
            )
        elif len(supporting_ids) > 0 and len(contradicting_ids) == 0:
            description = f"Consensus supporting evidence ({len(supporting_ids)} passages)."
        elif len(contradicting_ids) > 0 and len(supporting_ids) == 0:
            description = f"Consensus contradicting evidence ({len(contradicting_ids)} passages)."
        else:
            description = "All evaluated evidence is neutral or insufficient."

        return ConflictReport(
            conflict_detected=conflict_detected,
            conflict_score=conflict_score,
            support_mass=round(support_mass, 4),
            contradict_mass=round(contradict_mass, 4),
            supporting_ids=supporting_ids,
            contradicting_ids=contradicting_ids,
            neutral_ids=neutral_ids,
            supporting_sources=sorted(list(supporting_sources)),
            contradicting_sources=sorted(list(contradicting_sources)),
            description=description,
        )

"""Temporal reasoning and chronological consistency analyzer."""

from datetime import datetime
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field
from src.pipeline.schema import EvidencePassage


class TemporalReport(BaseModel):
    claim_years: List[int] = Field(default_factory=list, description="Years explicitly referenced in claim")
    is_present_oriented: bool = Field(default=False, description="Whether claim refers to current/latest state")
    has_temporal_mismatch: bool = Field(default=False, description="Whether temporal inconsistency is detected")
    temporal_uncertainty_penalty: float = Field(default=0.0, description="Penalty [0, 1] for temporal divergence")
    notes: str = Field(default="No temporal discrepancy detected.", description="Summary notes on temporal analysis")


class TemporalAnalyzer:
    """Analyzes temporal context, publication dates, and chronological validity."""

    PRESENT_MARKERS = {
        "currently", "now", "presently", "today", "latest", "current",
        "market leader", "is the", "ongoing", "active"
    }

    def __init__(self, outdated_penalty: float = 0.3, mismatch_penalty: float = 0.5):
        self.outdated_penalty = outdated_penalty
        self.mismatch_penalty = mismatch_penalty

    def extract_years(self, text: str) -> List[int]:
        """Extract explicit 4-digit calendar years from text."""
        matches = re.findall(r"\b(18\d\d|19\d\d|20\d\d)\b", text)
        return sorted(list({int(m) for m in matches}))

    def extract_date(self, date_str: Optional[str]) -> Optional[int]:
        """Extract year from an ISO date string or year string."""
        if not date_str:
            return None
        match = re.search(r"\b(18\d\d|19\d\d|20\d\d)\b", str(date_str))
        if match:
            return int(match.group(1))
        return None

    def analyze(self, claim: str, passages: List[EvidencePassage]) -> Tuple[List[EvidencePassage], TemporalReport]:
        """Assess temporal alignment between claim and retrieved evidence."""
        claim_years = self.extract_years(claim)
        claim_lower = claim.lower()
        is_present = any(marker in claim_lower for marker in self.PRESENT_MARKERS) and len(claim_years) == 0

        if not passages:
            return passages, TemporalReport(
                claim_years=claim_years,
                is_present_oriented=is_present,
                has_temporal_mismatch=False,
                temporal_uncertainty_penalty=0.0,
                notes="No evidence to assess for temporal consistency.",
            )

        # Inspect evidence dates
        evidence_dates: List[Tuple[EvidencePassage, Optional[int]]] = []
        all_passage_years: Set[int] = set()

        for p in passages:
            pub_year = self.extract_date(p.published_date)
            text_years = self.extract_years(p.text)
            ref_year = pub_year or (text_years[-1] if text_years else None)
            evidence_dates.append((p, ref_year))
            if ref_year:
                all_passage_years.add(ref_year)

        max_evidence_year = max(all_passage_years) if all_passage_years else None
        min_evidence_year = min(all_passage_years) if all_passage_years else None

        has_mismatch = False
        penalty = 0.0
        discrepancy_reasons = []

        for p, ref_year in evidence_dates:
            validity = 1.0
            note = "Temporally aligned."

            # Case 1: Claim is about current state, but older evidence contradicts newer evidence
            if is_present and ref_year and max_evidence_year and (max_evidence_year - ref_year >= 3):
                validity = max(0.2, 1.0 - self.outdated_penalty)
                note = f"Potentially outdated ({ref_year}) relative to newer evidence ({max_evidence_year})."
                has_mismatch = True
                discrepancy_reasons.append(note)

            # Case 2: Claim specifies a year, but evidence contradicts that timeline
            elif claim_years and ref_year:
                if ref_year not in claim_years:
                    # If evidence describes events years apart
                    diff = abs(claim_years[0] - ref_year)
                    if diff >= 2:
                        validity = max(0.3, 1.0 - (self.mismatch_penalty * min(1.0, diff / 10.0)))
                        note = f"Timeline gap: evidence refers to {ref_year}, while claim specifies {claim_years[0]}."
                        has_mismatch = True
                        discrepancy_reasons.append(note)

            p.temporal_validity = round(validity, 3)
            p.temporal_notes = note

        if has_mismatch:
            penalty = round(self.outdated_penalty if is_present else self.mismatch_penalty, 3)
            summary_notes = "; ".join(set(discrepancy_reasons))
        else:
            summary_notes = "Evidence chronology is consistent with claim temporal context."

        report = TemporalReport(
            claim_years=claim_years,
            is_present_oriented=is_present,
            has_temporal_mismatch=has_mismatch,
            temporal_uncertainty_penalty=penalty,
            notes=summary_notes,
        )

        return passages, report

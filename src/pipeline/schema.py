"""Structured data models for the verification pipeline."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class NLILabel(str, Enum):
    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    NEUTRAL = "NEUTRAL"


class EvidencePassage(BaseModel):
    id: str = Field(..., description="Unique passage or document ID")
    text: str = Field(..., description="Passage content")
    source: Optional[str] = Field(default="corpus", description="Origin source or title")
    published_date: Optional[str] = Field(default=None, description="ISO date or extracted year")
    retrieval_score: float = Field(default=0.0, description="Stage 1 retrieval score")
    relevance_score: float = Field(default=0.0, description="Stage 2 re-ranking relevance score")
    nli_label: Optional[NLILabel] = Field(default=None, description="Assigned NLI relationship")
    nli_score: Optional[float] = Field(default=None, description="Probability for the chosen NLI label")
    nli_probs: Optional[Dict[str, float]] = Field(default_factory=dict, description="Probabilities across classes")
    temporal_validity: Optional[float] = Field(default=1.0, description="Temporal appropriateness factor [0, 1]")
    temporal_notes: Optional[str] = Field(default=None, description="Notes on temporal consistency")


class SubClaim(BaseModel):
    id: str = Field(..., description="Unique subclaim ID")
    text: str = Field(..., description="Subclaim text proposition")
    verdict: Optional[Verdict] = Field(default=None, description="Subclaim verdict")
    confidence: Optional[float] = Field(default=None, description="Subclaim confidence")


class VerificationResult(BaseModel):
    claim: str = Field(..., description="Original claim text")
    verdict: Verdict = Field(..., description="Final verification verdict")
    confidence: float = Field(..., description="Calibrated confidence [0, 1]")
    uncertainty: float = Field(..., description="Uncertainty estimate [0, 1]")
    conflict_detected: bool = Field(default=False, description="Flag indicating conflicting evidence")
    subclaims: List[SubClaim] = Field(default_factory=list, description="Extracted atomic subclaims")
    evidence: List[EvidencePassage] = Field(default_factory=list, description="Top-k evaluated evidence passages")
    reasoning: str = Field(..., description="Traceable summary explanation of the verdict")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and stage execution metadata")

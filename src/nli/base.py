"""Base interface for Natural Language Inference (NLI) classifiers."""

from abc import ABC, abstractmethod
from typing import List, Tuple
from src.pipeline.schema import EvidencePassage


class BaseNLIClassifier(ABC):
    """Abstract interface for claim-evidence NLI classification."""

    @abstractmethod
    def classify_pairs(
        self,
        pairs: List[Tuple[str, str]],  # (claim, evidence_text)
    ) -> List[dict]:
        """Classify a list of (claim, evidence) pairs into NLI distributions.

        Returns list of dicts:
            {
                "label": NLILabel,
                "score": float,
                "probs": {"SUPPORT": float, "CONTRADICT": float, "NEUTRAL": float}
            }
        """
        pass

    @abstractmethod
    def evaluate_passages(
        self,
        claim: str,
        passages: List[EvidencePassage],
    ) -> List[EvidencePassage]:
        """Evaluate evidence passages against a claim and update passage NLI fields in-place."""
        pass

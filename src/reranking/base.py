"""Base interface for evidence re-ranking."""

from abc import ABC, abstractmethod
from typing import List
from src.pipeline.schema import EvidencePassage


class BaseReranker(ABC):
    """Abstract interface for passage re-ranking."""

    @abstractmethod
    def rerank(self, query: str, passages: List[EvidencePassage], top_k: int = 5) -> List[EvidencePassage]:
        """Re-rank candidate evidence passages relative to the query.

        Args:
            query: Claim or query string.
            passages: Candidate evidence passages from stage 1 retrieval.
            top_k: Number of passages to retain after re-ranking.

        Returns:
            Top-k re-ranked EvidencePassage objects with updated relevance_score.
        """
        pass

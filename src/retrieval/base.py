"""Base interface for evidence retrieval components."""

from abc import ABC, abstractmethod
from typing import List
from src.pipeline.schema import EvidencePassage


class BaseRetriever(ABC):
    """Abstract base class for evidence retrieval engines."""

    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[EvidencePassage]:
        """Search the evidence corpus for passages relevant to the query.

        Args:
            query: The search query string (e.g., claim).
            top_k: Number of candidate passages to return.

        Returns:
            List of ranked EvidencePassage objects.
        """
        pass

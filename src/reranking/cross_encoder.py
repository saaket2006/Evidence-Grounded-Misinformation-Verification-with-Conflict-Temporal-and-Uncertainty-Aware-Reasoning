"""Cross-encoder re-ranking engine for candidate evidence passages."""

import logging
from typing import List, Optional
import numpy as np
import torch
from sentence_transformers import CrossEncoder

from src.pipeline.schema import EvidencePassage
from src.reranking.base import BaseReranker

logger = logging.getLogger(__name__)


def sigmoid(x: float) -> float:
    """Compute numerical sigmoid."""
    return float(1.0 / (1.0 + np.exp(-x)))


class CrossEncoderReranker(BaseReranker):
    """Re-ranks candidate passages using a cross-encoder model."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "auto",
    ):
        self.model_name = model_name
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        self.model: Optional[CrossEncoder] = None

    def _ensure_model(self) -> CrossEncoder:
        if self.model is None:
            logger.info(f"Loading CrossEncoder re-ranking model: {self.model_name} on {self.device}")
            try:
                self.model = CrossEncoder(self.model_name, device=self.device)
            except Exception:
                self.model = CrossEncoder(self.model_name, device=self.device, local_files_only=True)
        return self.model

    def rerank(self, query: str, passages: List[EvidencePassage], top_k: int = 5) -> List[EvidencePassage]:
        if not passages:
            return []

        try:
            model = self._ensure_model()
            pairs = [[query, p.text] for p in passages]
            raw_scores = model.predict(pairs, show_progress_bar=False)

            # Assign sigmoid-normalized relevance scores
            for p, score in zip(passages, raw_scores):
                # Sigmoid maps logit to [0, 1]
                p.relevance_score = round(sigmoid(float(score)), 4)

            # Sort descending by relevance score
            sorted_passages = sorted(passages, key=lambda p: p.relevance_score, reverse=True)
            return sorted_passages[:top_k]
        except Exception as e:
            logger.warning(f"CrossEncoder re-ranking encountered error ({e}). Falling back to retrieval scores.")
            sorted_passages = sorted(passages, key=lambda p: p.retrieval_score, reverse=True)
            return sorted_passages[:top_k]

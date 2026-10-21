"""Hybrid retrieval combining lexical (BM25) and dense semantic search."""

from typing import Dict, List
from src.pipeline.schema import EvidencePassage
from src.retrieval.base import BaseRetriever
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseRetriever


class HybridRetriever(BaseRetriever):
    """Combines BM25 lexical and Dense semantic retrieval."""

    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        dense_retriever: DenseRetriever,
        weight_bm25: float = 0.5,
        weight_dense: float = 0.5,
        rrf_k: int = 60,
        fusion_method: str = "linear",  # "linear" or "rrf"
    ):
        self.bm25 = bm25_retriever
        self.dense = dense_retriever
        self.weight_bm25 = weight_bm25
        self.weight_dense = weight_dense
        self.rrf_k = rrf_k
        self.fusion_method = fusion_method

    def search(self, query: str, top_k: int = 10) -> List[EvidencePassage]:
        """Execute hybrid search using configured fusion strategy."""
        fetch_k = max(top_k * 2, 20)
        bm25_results = self.bm25.search(query, top_k=fetch_k)
        dense_results = self.dense.search(query, top_k=fetch_k)

        if not bm25_results and not dense_results:
            return []
        if not bm25_results:
            return dense_results[:top_k]
        if not dense_results:
            return bm25_results[:top_k]

        passage_map: Dict[str, EvidencePassage] = {}
        combined_scores: Dict[str, float] = {}

        if self.fusion_method == "rrf":
            # Reciprocal Rank Fusion
            for rank, p in enumerate(bm25_results):
                passage_map[p.id] = p
                combined_scores[p.id] = combined_scores.get(p.id, 0.0) + (self.weight_bm25 / (self.rrf_k + rank + 1))

            for rank, p in enumerate(dense_results):
                passage_map[p.id] = p
                combined_scores[p.id] = combined_scores.get(p.id, 0.0) + (self.weight_dense / (self.rrf_k + rank + 1))
        else:
            # Linear Score Combination
            for p in bm25_results:
                passage_map[p.id] = p
                combined_scores[p.id] = combined_scores.get(p.id, 0.0) + (self.weight_bm25 * p.retrieval_score)

            for p in dense_results:
                passage_map[p.id] = p
                combined_scores[p.id] = combined_scores.get(p.id, 0.0) + (self.weight_dense * p.retrieval_score)

        # Sort descending
        ranked_doc_ids = sorted(combined_scores.keys(), key=lambda doc_id: combined_scores[doc_id], reverse=True)[
            :top_k
        ]

        # Rescale scores to [0, 1]
        max_combined = max(combined_scores.values()) if combined_scores else 1.0
        final_passages = []
        for doc_id in ranked_doc_ids:
            p = passage_map[doc_id]
            raw_score = combined_scores[doc_id]
            norm_score = raw_score / max_combined if max_combined > 0 else raw_score
            p.retrieval_score = round(norm_score, 4)
            p.relevance_score = p.retrieval_score
            final_passages.append(p)

        return final_passages

"""Lexical BM25 retrieval engine."""

import pickle
import re
from pathlib import Path
from typing import List, Optional
from rank_bm25 import BM25Okapi

from src.pipeline.schema import EvidencePassage
from src.retrieval.base import BaseRetriever
from src.retrieval.corpus import CorpusManager


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric lowercasing tokenizer for BM25."""
    return re.findall(r"\b\w+\b", text.lower())


class BM25Retriever(BaseRetriever):
    """Lexical retriever based on Okapi BM25."""

    def __init__(self, corpus_manager: CorpusManager, index_path: Optional[str | Path] = None):
        self.corpus_manager = corpus_manager
        self.index_path = Path(index_path) if index_path else None
        self.bm25: Optional[BM25Okapi] = None
        self.doc_ids: List[str] = []

        if self.index_path and self.index_path.exists():
            self.load_index(self.index_path)
        elif len(self.corpus_manager) > 0:
            self.build_index()

    def build_index(self) -> None:
        """Build BM25 index from corpus manager documents."""
        self.doc_ids = []
        tokenized_corpus = []
        for doc in self.corpus_manager.documents:
            # Combine title and text for index representation
            combined = f"{doc.get('title', '')} {doc.get('text', '')}"
            tokens = tokenize(combined)
            tokenized_corpus.append(tokens)
            self.doc_ids.append(doc["id"])

        if tokenized_corpus:
            self.bm25 = BM25Okapi(tokenized_corpus)

    def save_index(self, path: Optional[str | Path] = None) -> None:
        """Save BM25 index and doc_ids to disk."""
        target_path = Path(path) if path else self.index_path
        if not target_path:
            raise ValueError("No path specified to save BM25 index.")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "doc_ids": self.doc_ids}, f)

    def load_index(self, path: str | Path) -> None:
        """Load precomputed BM25 index from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.bm25 = data["bm25"]
            self.doc_ids = data["doc_ids"]

    def search(self, query: str, top_k: int = 10) -> List[EvidencePassage]:
        """Search BM25 index for the given query."""
        if not self.bm25 or not self.doc_ids:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0.0:
                continue
            # Rational saturation normalization: maps raw BM25 [0, inf) to [0, 1)
            # A raw score of 10.0 maps to 0.5, while weak incidental hits (<6.0) stay < 0.4
            normalized_score = min(score / (score + 10.0), 1.0)
            doc_id = self.doc_ids[idx]
            passage = self.corpus_manager.to_evidence_passage(doc_id, score=round(normalized_score, 4))
            if passage:
                results.append(passage)

        return results

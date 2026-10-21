"""Dense semantic retrieval engine using Sentence Transformers."""

from pathlib import Path
from typing import List, Optional
import torch
from sentence_transformers import SentenceTransformer

from src.pipeline.schema import EvidencePassage
from src.retrieval.base import BaseRetriever
from src.retrieval.corpus import CorpusManager


class DenseRetriever(BaseRetriever):
    """Dense retriever using bi-encoder sentence embeddings."""

    def __init__(
        self,
        corpus_manager: CorpusManager,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_path: Optional[str | Path] = None,
        device: str = "auto",
    ):
        self.corpus_manager = corpus_manager
        self.model_name = model_name
        self.index_path = Path(index_path) if index_path else None

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model: Optional[SentenceTransformer] = None
        self.doc_ids: List[str] = []
        self.embeddings: Optional[torch.Tensor] = None

        if self.index_path and self.index_path.exists():
            self.load_index(self.index_path)

    def _ensure_model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name, device=self.device)
            except Exception:
                # Fallback to local cached files if network is unavailable
                self.model = SentenceTransformer(self.model_name, device=self.device, local_files_only=True)
        return self.model

    def build_index(self, batch_size: int = 32) -> None:
        """Encode all documents in the corpus and build dense tensor index."""
        model = self._ensure_model()
        self.doc_ids = []
        texts = []

        for doc in self.corpus_manager.documents:
            # Combine title and body text for semantic encoding
            text = f"{doc.get('title', '')}: {doc.get('text', '')}"
            texts.append(text)
            self.doc_ids.append(doc["id"])

        if texts:
            with torch.no_grad():
                embeds = model.encode(
                    texts,
                    convert_to_tensor=True,
                    batch_size=batch_size,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                )
                self.embeddings = embeds.to(self.device)

    def save_index(self, path: Optional[str | Path] = None) -> None:
        """Save embeddings and document IDs to disk."""
        target_path = Path(path) if path else self.index_path
        if not target_path:
            raise ValueError("No path specified to save dense index.")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "embeddings": self.embeddings.cpu() if self.embeddings is not None else None,
                "doc_ids": self.doc_ids,
                "model_name": self.model_name,
            },
            target_path,
        )

    def load_index(self, path: str | Path) -> None:
        """Load embeddings and document IDs from disk."""
        data = torch.load(path, map_location=self.device)
        self.embeddings = data["embeddings"].to(self.device) if data["embeddings"] is not None else None
        self.doc_ids = data["doc_ids"]
        self.model_name = data.get("model_name", self.model_name)

    def search(self, query: str, top_k: int = 10) -> List[EvidencePassage]:
        """Search dense embeddings using cosine similarity."""
        if self.embeddings is None or not self.doc_ids:
            return []

        model = self._ensure_model()
        with torch.no_grad():
            query_emb = model.encode(query, convert_to_tensor=True, normalize_embeddings=True).to(self.device)
            # Dot product between normalized embeddings is cosine similarity
            scores = torch.mv(self.embeddings, query_emb)
            top_k_actual = min(top_k, len(self.doc_ids))
            top_scores, top_indices = torch.topk(scores, k=top_k_actual)

        results = []
        for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
            doc_id = self.doc_ids[idx]
            # Rescale cosine score from [-1, 1] to [0, 1]
            norm_score = max(0.0, min(1.0, (score + 1.0) / 2.0))
            passage = self.corpus_manager.to_evidence_passage(doc_id, score=norm_score)
            if passage:
                results.append(passage)

        return results

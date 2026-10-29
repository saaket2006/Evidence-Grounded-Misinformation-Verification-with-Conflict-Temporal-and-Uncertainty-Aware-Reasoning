"""Corpus management and document loading."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.pipeline.schema import EvidencePassage


class CorpusManager:
    """Manages passage loading, lookup, and metadata for the evidence corpus."""

    def __init__(self, corpus_path: str | Path):
        self.corpus_path = Path(corpus_path)
        self.documents: List[Dict[str, Any]] = []
        self.doc_map: Dict[str, Dict[str, Any]] = {}
        if self.corpus_path.exists():
            self.load()

    def load(self) -> None:
        """Load corpus JSONL into memory."""
        self.documents = []
        self.doc_map = {}
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                doc = json.loads(line)
                self.documents.append(doc)
                self.doc_map[doc["id"]] = doc

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve document by ID."""
        return self.doc_map.get(doc_id)

    def to_evidence_passage(self, doc_id: str, score: float = 0.0) -> Optional[EvidencePassage]:
        """Convert a document into a pipeline EvidencePassage object."""
        doc = self.get_document(doc_id)
        if not doc:
            return None
        return EvidencePassage(
            id=doc["id"],
            doc_id=doc["id"],
            text=doc.get("text", ""),
            source=doc.get("title", "Corpus"),
            published_date=doc.get("published_date"),
            retrieval_score=score,
            relevance_score=score,
        )

    def __len__(self) -> int:
        return len(self.documents)

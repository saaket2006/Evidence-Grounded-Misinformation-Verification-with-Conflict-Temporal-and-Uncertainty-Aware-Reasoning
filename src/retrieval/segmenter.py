"""Evidence granularity segmentation engine.

Segments retrieved candidate documents into bounded passages or individual sentences
for granular cross-encoder re-ranking and Natural Language Inference (NLI).
Preserves document provenance, metadata, and handles boundary edge cases.
"""

import logging
import re
from typing import List, Optional
from src.pipeline.schema import EvidencePassage

logger = logging.getLogger(__name__)

# Common abbreviations to prevent premature sentence splitting
_COMMON_ABBREVIATIONS = [
    "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.", "vs.", "etc.",
    "e.g.", "i.e.", "U.S.", "U.K.", "Oct.", "Nov.", "Dec.", "Jan.", "Feb.",
    "Mar.", "Apr.", "Jun.", "Jul.", "Aug.", "Sep.", "No.", "Vol.", "p.", "pp."
]


class EvidenceSegmenter:
    """Configurable segmenter decomposing long documents into granular evidence units."""

    def __init__(
        self,
        enabled: bool = True,
        unit: str = "sentence",
        max_sentences_per_passage: int = 1,
        max_characters: int = 400,
        min_characters: int = 15,
        overlap_sentences: int = 0,
    ):
        """Args:
            enabled: If False, passes documents through without segmentation.
            unit: Granularity level: 'sentence', 'bounded_passage', or 'document'.
            max_sentences_per_passage: Target sentences per segmented passage (1 for sentence-level).
            max_characters: Upper character bound per passage to respect model token limits.
            min_characters: Minimum character count to filter out noisy fragments.
            overlap_sentences: Number of overlapping sentences between consecutive passages.
        """
        self.enabled = enabled
        self.unit = unit.lower()
        self.max_sentences_per_passage = max(1, max_sentences_per_passage)
        self.max_characters = max_characters
        self.min_characters = min_characters
        self.overlap_sentences = max(0, overlap_sentences)

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while protecting abbreviations and special boundaries."""
        if not text:
            return []

        sanitized = text.replace("\r\n", " ").replace("\n", " ").strip()
        if not sanitized:
            return []

        # Temporarily substitute known abbreviations
        placeholders = {}
        for i, abbr in enumerate(_COMMON_ABBREVIATIONS):
            token = f"__ABBR_TOKEN_{i}__"
            if abbr in sanitized:
                sanitized = sanitized.replace(abbr, token)
                placeholders[token] = abbr

        # Split on sentence terminals followed by whitespace and capital/quote/parenthesis
        raw_splits = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'\(\[])', sanitized)

        sentences = []
        for s in raw_splits:
            s = s.strip()
            if not s:
                continue
            # Restore protected abbreviation tokens
            for token, abbr in placeholders.items():
                s = s.replace(token, abbr)
            sentences.append(s)

        # Fallback if regex produced nothing
        if not sentences and sanitized:
            sentences = [sanitized]

        return sentences

    def segment_passage(self, passage: EvidencePassage) -> List[EvidencePassage]:
        """Segment a single document passage into bounded passage units."""
        if not self.enabled or self.unit == "document":
            p_copy = passage.model_copy()
            if not p_copy.doc_id:
                p_copy.doc_id = p_copy.id.split("#")[0]
            return [p_copy]

        text = (passage.text or "").strip()
        if len(text) < self.min_characters:
            p_copy = passage.model_copy()
            if not p_copy.doc_id:
                p_copy.doc_id = p_copy.id.split("#")[0]
            return [p_copy]

        sentences = self.split_into_sentences(text)
        if not sentences:
            p_copy = passage.model_copy()
            if not p_copy.doc_id:
                p_copy.doc_id = p_copy.id.split("#")[0]
            return [p_copy]

        # If already a single sentence within bounds, preserve intact
        if len(sentences) == 1 and len(sentences[0]) <= self.max_characters:
            p_copy = passage.model_copy()
            if not p_copy.doc_id:
                p_copy.doc_id = p_copy.id.split("#")[0]
            return [p_copy]

        # Group sentences into bounded chunks
        chunks: List[str] = []
        step = max(1, self.max_sentences_per_passage - self.overlap_sentences)
        idx = 0

        while idx < len(sentences):
            chunk_sents = sentences[idx : idx + self.max_sentences_per_passage]
            chunk_text = " ".join(chunk_sents).strip()

            # Enforce max character limit by trimming sentence count if necessary
            while len(chunk_text) > self.max_characters and len(chunk_sents) > 1:
                chunk_sents = chunk_sents[:-1]
                chunk_text = " ".join(chunk_sents).strip()

            # Bounded passage character truncation as a safeguard against single run-on sentences
            if len(chunk_text) > self.max_characters:
                chunk_text = chunk_text[: self.max_characters].rsplit(" ", 1)[0] + "..."

            if len(chunk_text) >= self.min_characters:
                chunks.append(chunk_text)

            idx += step
            if step == 0:
                break

        # If chunking produced nothing, fall back to original
        if not chunks:
            p_copy = passage.model_copy()
            if not p_copy.doc_id:
                p_copy.doc_id = p_copy.id.split("#")[0]
            return [p_copy]

        doc_id = passage.doc_id or passage.id.split("#")[0]
        segmented_passages: List[EvidencePassage] = []

        for c_idx, chunk_content in enumerate(chunks):
            seg_id = f"{doc_id}#s{c_idx}" if len(chunks) > 1 else doc_id
            seg_passage = EvidencePassage(
                id=seg_id,
                doc_id=doc_id,
                text=chunk_content,
                source=passage.source,
                published_date=passage.published_date,
                retrieval_score=passage.retrieval_score,
                relevance_score=passage.relevance_score,
                temporal_validity=passage.temporal_validity,
                temporal_notes=passage.temporal_notes,
            )
            segmented_passages.append(seg_passage)

        return segmented_passages

    def segment_passages(self, passages: List[EvidencePassage]) -> List[EvidencePassage]:
        """Segment a batch of evidence passages/documents, preserving ordering and provenance."""
        if not passages or not self.enabled or self.unit == "document":
            return [
                p.model_copy(update={"doc_id": p.doc_id or p.id.split("#")[0]})
                for p in passages
            ]

        results: List[EvidencePassage] = []
        for p in passages:
            results.extend(self.segment_passage(p))

        return results

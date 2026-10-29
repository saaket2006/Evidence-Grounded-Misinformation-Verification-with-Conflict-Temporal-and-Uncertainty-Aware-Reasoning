"""Regression tests for Fix C: Safe evidence passage HTML escaping and XSS prevention in UI.

Verifies that:
1. Script tags and HTML payloads in evidence text are escaped rather than rendered as executable HTML.
2. HTML special characters in source names, dates, and temporal notes are escaped.
3. Missing dates, notes, and optional metadata fields are handled safely.
4. Ordinary evidence passages render with complete text, metadata, and CSS card classes.
"""

import pytest

from src.pipeline.schema import EvidencePassage, NLILabel
from ui.app import format_passage_html


def test_xss_script_tags_escaped_in_passage_text():
    """Verify that script tags in retrieved evidence passages are escaped into text."""
    malicious_text = "<script>alert('xss')</script>"
    passage = EvidencePassage(
        id="p_xss",
        text=malicious_text,
        source="Untrusted Blog",
        retrieval_score=0.9,
        relevance_score=0.9,
        nli_label=NLILabel.SUPPORT,
        nli_score=0.92,
    )

    card_html = format_passage_html(passage, "evidence-support")

    # Script tag must not appear unescaped in HTML
    assert "<script>" not in card_html
    assert "</script>" not in card_html
    # Escaped entity representations must be present
    assert "&lt;script&gt;" in card_html
    assert "&lt;/script&gt;" in card_html


def test_html_special_chars_escaped_in_metadata():
    """Verify that HTML special characters in source, date, and temporal notes are escaped."""
    passage = EvidencePassage(
        id="p_meta",
        text="Normal evidence text.",
        source='<img src=x onerror=alert("hacked")> & "News"',
        published_date="<b>2024-01-01</b>",
        temporal_notes="Temporal mismatch: claim < 2024 & year > 2020",
        retrieval_score=0.85,
        relevance_score=0.85,
        nli_label=NLILabel.CONTRADICT,
        nli_score=0.88,
    )

    card_html = format_passage_html(passage, "evidence-contradict")

    # Verify no unescaped tags or executable markup from metadata
    assert "<img" not in card_html
    assert "<b>2024-01-01</b>" not in card_html

    # Verify escaped equivalents
    assert "&lt;img" in card_html
    assert "&amp;" in card_html
    assert "&quot;hacked&quot;" in card_html
    assert "&lt;b&gt;2024-01-01&lt;/b&gt;" in card_html
    assert "&lt; 2024" in card_html


def test_missing_optional_fields_handled_safely():
    """Verify that passages with None / missing metadata are handled without crashing."""
    passage = EvidencePassage(
        id="p_sparse",
        text="Evidence text without metadata.",
        source=None,
        published_date=None,
        temporal_notes=None,
        retrieval_score=0.5,
        relevance_score=0.5,
        nli_label=None,
        nli_score=None,
    )

    card_html = format_passage_html(passage, "evidence-neutral")

    assert "evidence-neutral" in card_html
    assert "Corpus" in card_html
    assert "Date:</b> N/A" in card_html
    assert "NLI Relation:</b> <code>N/A</code>" in card_html
    assert "Evidence text without metadata." in card_html


def test_ordinary_passage_formatting():
    """Verify that ordinary, clean evidence passages format with correct structure and values."""
    passage = EvidencePassage(
        id="p_clean",
        text="Alan Turing was born in Maida Vale, London.",
        source="Wikipedia: Alan Turing",
        published_date="1912-06-23",
        temporal_notes="Historical consensus.",
        retrieval_score=0.95,
        relevance_score=0.91,
        temporal_validity=1.0,
        nli_label=NLILabel.SUPPORT,
        nli_score=0.965,
    )

    card_html = format_passage_html(passage, "evidence-support")

    assert 'class="evidence-card evidence-support"' in card_html
    assert "Wikipedia: Alan Turing" in card_html
    assert "1912-06-23" in card_html
    assert "<code>SUPPORT</code>" in card_html
    assert "96.5%" in card_html
    assert "0.91" in card_html
    assert "1.00" in card_html
    assert "Alan Turing was born in Maida Vale, London." in card_html
    assert "Historical consensus." in card_html

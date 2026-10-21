"""Unit tests for temporal reasoning module."""

import pytest
from src.pipeline.schema import EvidencePassage
from src.temporal.analyzer import TemporalAnalyzer


def test_matching_dates():
    analyzer = TemporalAnalyzer()
    claim = "NASA Perseverance landed on Mars in 2021."
    passages = [
        EvidencePassage(
            id="p1",
            text="The rover landed on Mars on February 18, 2021.",
            published_date="2021-02-19",
        )
    ]
    updated, report = analyzer.analyze(claim, passages)
    assert not report.has_temporal_mismatch
    assert report.temporal_uncertainty_penalty == 0.0
    assert updated[0].temporal_validity == 1.0


def test_outdated_evidence():
    analyzer = TemporalAnalyzer(outdated_penalty=0.3)
    claim = "Acme Corp is currently the market leader."
    passages = [
        EvidencePassage(
            id="p1",
            text="In 2019, Acme Corp was the market leader.",
            published_date="2019-01-01",
        ),
        EvidencePassage(
            id="p2",
            text="In 2024, Zenith overtook Acme.",
            published_date="2024-05-01",
        ),
    ]
    updated, report = analyzer.analyze(claim, passages)
    assert report.is_present_oriented
    assert report.has_temporal_mismatch
    # 2019 passage should be flagged as outdated
    assert updated[0].temporal_validity < 1.0
    assert "outdated" in updated[0].temporal_notes.lower()


def test_conflicting_temporal_evidence():
    analyzer = TemporalAnalyzer(mismatch_penalty=0.5)
    claim = "Alan Turing died in 1980."
    passages = [
        EvidencePassage(
            id="p1",
            text="Alan Turing died in 1954 from poisoning.",
            published_date="1954-06-10",
        )
    ]
    updated, report = analyzer.analyze(claim, passages)
    assert report.has_temporal_mismatch
    assert updated[0].temporal_validity < 1.0
    assert "Timeline gap" in updated[0].temporal_notes


def test_missing_dates():
    analyzer = TemporalAnalyzer()
    claim = "The Great Wall of China is built of stone."
    passages = [
        EvidencePassage(
            id="p1",
            text="The Great Wall consists of stone and earth fortifications.",
            published_date=None,
        )
    ]
    updated, report = analyzer.analyze(claim, passages)
    assert not report.has_temporal_mismatch
    assert updated[0].temporal_validity == 1.0

"""Unit tests for conflict analysis module."""

import pytest
from src.conflict.detector import ConflictDetector
from src.pipeline.schema import EvidencePassage, NLILabel


def test_only_supporting_evidence():
    detector = ConflictDetector()
    passages = [
        EvidencePassage(
            id="p1",
            text="Evidence A",
            relevance_score=0.9,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.9, "CONTRADICT": 0.05, "NEUTRAL": 0.05},
        ),
        EvidencePassage(
            id="p2",
            text="Evidence B",
            relevance_score=0.85,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.85, "CONTRADICT": 0.05, "NEUTRAL": 0.1},
        ),
    ]
    report = detector.analyze(passages)
    assert not report.conflict_detected
    assert report.conflict_score == 0.0
    assert len(report.supporting_ids) == 2
    assert len(report.contradicting_ids) == 0


def test_only_contradicting_evidence():
    detector = ConflictDetector()
    passages = [
        EvidencePassage(
            id="p1",
            text="Evidence A",
            relevance_score=0.9,
            nli_label=NLILabel.CONTRADICT,
            nli_probs={"SUPPORT": 0.05, "CONTRADICT": 0.9, "NEUTRAL": 0.05},
        ),
    ]
    report = detector.analyze(passages)
    assert not report.conflict_detected
    assert report.conflict_score == 0.0
    assert len(report.contradicting_ids) == 1


def test_mixed_conflicting_evidence():
    detector = ConflictDetector()
    passages = [
        EvidencePassage(
            id="p1",
            text="Evidence Supporting",
            relevance_score=0.9,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.9, "CONTRADICT": 0.05, "NEUTRAL": 0.05},
        ),
        EvidencePassage(
            id="p2",
            text="Evidence Contradicting",
            relevance_score=0.85,
            nli_label=NLILabel.CONTRADICT,
            nli_probs={"SUPPORT": 0.05, "CONTRADICT": 0.85, "NEUTRAL": 0.1},
        ),
    ]
    report = detector.analyze(passages)
    assert report.conflict_detected
    assert report.conflict_score > 0.5
    assert len(report.supporting_ids) == 1
    assert len(report.contradicting_ids) == 1

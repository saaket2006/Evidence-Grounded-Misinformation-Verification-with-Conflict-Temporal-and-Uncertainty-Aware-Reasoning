"""Unit tests for uncertainty estimation module."""

import pytest
from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage, NLILabel
from src.temporal.analyzer import TemporalReport
from src.uncertainty.estimator import UncertaintyEstimator


@pytest.fixture
def estimator():
    return UncertaintyEstimator()


def test_strong_agreement(estimator):
    agg = AggregationResult(
        support_prob=0.95,
        contradict_prob=0.02,
        neutral_prob=0.03,
        effective_mass=2.0,
        num_supporting=2,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    temporal = TemporalReport(has_temporal_mismatch=False, temporal_uncertainty_penalty=0.0)
    passages = [
        EvidencePassage(id="p1", text="ev1", relevance_score=0.9),
        EvidencePassage(id="p2", text="ev2", relevance_score=0.88),
    ]

    profile = estimator.estimate(agg, conflict, temporal, passages)
    assert profile.total_uncertainty < 0.35
    assert profile.calibrated_confidence > 0.65


def test_weak_evidence(estimator):
    agg = AggregationResult(
        support_prob=0.45,
        contradict_prob=0.15,
        neutral_prob=0.40,
        effective_mass=0.2,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    temporal = TemporalReport(has_temporal_mismatch=False, temporal_uncertainty_penalty=0.0)
    passages = [EvidencePassage(id="p1", text="ev", relevance_score=0.2)]

    profile = estimator.estimate(agg, conflict, temporal, passages)
    # Retrieval deficit and high entropy should raise uncertainty
    assert profile.total_uncertainty > 0.50


def test_conflicting_evidence(estimator):
    agg = AggregationResult(
        support_prob=0.50,
        contradict_prob=0.50,
        neutral_prob=0.0,
        effective_mass=1.8,
    )
    conflict = ConflictReport(conflict_detected=True, conflict_score=0.95)
    temporal = TemporalReport(has_temporal_mismatch=False, temporal_uncertainty_penalty=0.0)
    passages = [
        EvidencePassage(id="p1", text="sup", relevance_score=0.9),
        EvidencePassage(id="p2", text="con", relevance_score=0.9),
    ]

    profile = estimator.estimate(agg, conflict, temporal, passages)
    assert profile.conflict_uncertainty > 0.8
    assert profile.total_uncertainty > 0.55


def test_insufficient_evidence(estimator):
    agg = AggregationResult(
        support_prob=0.0,
        contradict_prob=0.0,
        neutral_prob=1.0,
        effective_mass=0.0,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    temporal = TemporalReport(has_temporal_mismatch=False, temporal_uncertainty_penalty=0.0)
    passages = []

    profile = estimator.estimate(agg, conflict, temporal, passages)
    # Zero passages -> 1.0 retrieval deficit
    assert profile.retrieval_deficit_uncertainty == 1.0
    assert profile.calibrated_confidence < 0.5

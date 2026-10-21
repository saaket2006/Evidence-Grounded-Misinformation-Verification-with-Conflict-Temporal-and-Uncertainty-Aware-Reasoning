"""Unit tests for final decision and abstention policy."""

import pytest
from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.decision.decider import VerificationDecider
from src.pipeline.schema import Verdict
from src.uncertainty.estimator import UncertaintyProfile


@pytest.fixture
def decider():
    return VerificationDecider(
        support_threshold=0.55,
        contradict_threshold=0.55,
        max_uncertainty_threshold=0.60,
    )


def test_verdict_supported(decider):
    agg = AggregationResult(
        support_prob=0.85,
        contradict_prob=0.05,
        neutral_prob=0.10,
        effective_mass=1.5,
        num_supporting=2,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    unc = UncertaintyProfile(
        total_uncertainty=0.25,
        calibrated_confidence=0.75,
        entropy_uncertainty=0.2,
        conflict_uncertainty=0.0,
        retrieval_deficit_uncertainty=0.1,
        temporal_uncertainty=0.0,
    )
    verdict, reason = decider.decide(agg, conflict, unc)
    assert verdict == Verdict.SUPPORTED


def test_verdict_contradicted(decider):
    agg = AggregationResult(
        support_prob=0.05,
        contradict_prob=0.88,
        neutral_prob=0.07,
        effective_mass=1.2,
        num_contradicting=2,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    unc = UncertaintyProfile(
        total_uncertainty=0.25,
        calibrated_confidence=0.75,
        entropy_uncertainty=0.2,
        conflict_uncertainty=0.0,
        retrieval_deficit_uncertainty=0.1,
        temporal_uncertainty=0.0,
    )
    verdict, reason = decider.decide(agg, conflict, unc)
    assert verdict == Verdict.CONTRADICTED


def test_verdict_insufficient_evidence_by_conflict(decider):
    agg = AggregationResult(
        support_prob=0.52,
        contradict_prob=0.48,
        neutral_prob=0.0,
        effective_mass=1.5,
    )
    conflict = ConflictReport(
        conflict_detected=True,
        conflict_score=0.85,
        support_mass=0.8,
        contradict_mass=0.7,
    )
    unc = UncertaintyProfile(
        total_uncertainty=0.65,
        calibrated_confidence=0.35,
        entropy_uncertainty=0.7,
        conflict_uncertainty=0.85,
        retrieval_deficit_uncertainty=0.1,
        temporal_uncertainty=0.0,
    )
    verdict, reason = decider.decide(agg, conflict, unc)
    assert verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert "conflict" in reason.lower()


def test_verdict_insufficient_evidence_by_empty(decider):
    agg = AggregationResult(effective_mass=0.0)
    conflict = ConflictReport()
    unc = UncertaintyProfile(
        total_uncertainty=1.0,
        calibrated_confidence=0.0,
        entropy_uncertainty=0.0,
        conflict_uncertainty=0.0,
        retrieval_deficit_uncertainty=1.0,
        temporal_uncertainty=0.0,
    )
    verdict, reason = decider.decide(agg, conflict, unc)
    assert verdict == Verdict.INSUFFICIENT_EVIDENCE

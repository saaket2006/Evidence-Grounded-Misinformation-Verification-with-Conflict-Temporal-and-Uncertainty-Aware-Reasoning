"""Regression tests for Fix B: Evidence-based verdict and abstention policy integrity.

Verifies that:
1. An advisor suggesting SUPPORTED cannot override an evidence-based INSUFFICIENT_EVIDENCE result.
2. An advisor suggesting CONTRADICTED cannot override an evidence-based INSUFFICIENT_EVIDENCE result.
3. An advisor suggesting a different decisive verdict cannot silently replace the decider's result.
4. Missing, failing, or malformed advisor output does not break the pipeline.
5. Verdict, calibrated confidence, uncertainty, and explanation remain structurally consistent.
"""

from unittest.mock import MagicMock
import pytest

from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage, NLILabel, SubClaim, Verdict
from src.pipeline.verifier import MisinformationVerifier
from src.reasoning.engine import ReasoningAdvice
from src.temporal.analyzer import TemporalReport
from src.uncertainty.estimator import UncertaintyProfile


@pytest.fixture
def mock_verifier():
    """Create a verifier instance with fast mocked subcomponents."""
    # We bypass heavy model initialization by instantiating directly or patching
    verifier = MisinformationVerifier.__new__(MisinformationVerifier)
    verifier.config = {}
    verifier.enable_decomposition = False
    verifier.retrieval_mode = "hybrid"
    verifier.use_reranking = False
    verifier.reranker = None
    verifier.evidence_segmenter = None
    verifier.use_temporal = False
    verifier.use_conflict = False
    verifier.top_k_evidence = 3

    verifier.decomposer = MagicMock()
    verifier.decomposer.decompose.return_value = [SubClaim(id="sc1", text="Test claim")]

    verifier._retrieve_candidates = MagicMock(return_value=[
        EvidencePassage(id="p1", text="Sample evidence", retrieval_score=0.8, relevance_score=0.8)
    ])

    verifier.nli_classifier = MagicMock()
    verifier.nli_classifier.evaluate_passages.side_effect = lambda c, p: p

    verifier.temporal_analyzer = MagicMock()
    verifier.temporal_analyzer.analyze.return_value = ([], TemporalReport())

    verifier.conflict_detector = MagicMock()
    verifier.conflict_detector.analyze.return_value = ConflictReport()

    verifier.aggregator = MagicMock()
    verifier.aggregator.aggregate.return_value = AggregationResult(
        support_prob=0.33, contradict_prob=0.33, neutral_prob=0.34, effective_mass=0.5
    )

    verifier.uncertainty_estimator = MagicMock()
    verifier.uncertainty_estimator.estimate.return_value = UncertaintyProfile(
        calibrated_confidence=0.45,
        total_uncertainty=0.55,
        entropy_uncertainty=0.2,
        conflict_uncertainty=0.1,
        retrieval_deficit_uncertainty=0.15,
        temporal_uncertainty=0.1,
    )

    verifier.decider = MagicMock()
    verifier.reasoning_engine = MagicMock()

    return verifier


def test_advisor_cannot_override_insufficient_evidence_with_support(mock_verifier):
    """An advisor suggesting SUPPORTED cannot override INSUFFICIENT_EVIDENCE."""
    mock_verifier.decider.decide.return_value = (
        Verdict.INSUFFICIENT_EVIDENCE,
        "Abstained due to insufficient evidence mass.",
    )
    mock_verifier.reasoning_engine.reason.return_value = ReasoningAdvice(
        synthesized_explanation="Advisor asserts claim is supported by world knowledge.",
        suggested_verdict=Verdict.SUPPORTED,
        advice_confidence_modifier=0.2,
        llm_executed=True,
    )

    result = mock_verifier.verify("Unverifiable claim")

    assert result.verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert result.confidence == 0.45
    assert result.uncertainty == 0.55
    assert result.metadata["reasoning"]["suggested_verdict"] == Verdict.SUPPORTED.value


def test_advisor_cannot_override_insufficient_evidence_with_contradiction(mock_verifier):
    """An advisor suggesting CONTRADICTED cannot override INSUFFICIENT_EVIDENCE."""
    mock_verifier.decider.decide.return_value = (
        Verdict.INSUFFICIENT_EVIDENCE,
        "Abstained due to conflicting and weak signals.",
    )
    mock_verifier.reasoning_engine.reason.return_value = ReasoningAdvice(
        synthesized_explanation="Advisor asserts claim is refuted.",
        suggested_verdict=Verdict.CONTRADICTED,
        llm_executed=True,
    )

    result = mock_verifier.verify("Contested claim")

    assert result.verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert result.confidence == 0.45
    assert result.uncertainty == 0.55


def test_advisor_cannot_override_decisive_verdict(mock_verifier):
    """An advisor suggesting a differing verdict cannot override decider's SUPPORTED verdict."""
    mock_verifier.decider.decide.return_value = (
        Verdict.SUPPORTED,
        "Empirical evidence mass decisively supports claim.",
    )
    mock_verifier.uncertainty_estimator.estimate.return_value = UncertaintyProfile(
        calibrated_confidence=0.92,
        total_uncertainty=0.08,
        entropy_uncertainty=0.03,
        conflict_uncertainty=0.02,
        retrieval_deficit_uncertainty=0.02,
        temporal_uncertainty=0.01,
    )
    mock_verifier.reasoning_engine.reason.return_value = ReasoningAdvice(
        synthesized_explanation="Advisor hallucinates contradiction.",
        suggested_verdict=Verdict.CONTRADICTED,
        llm_executed=True,
    )

    result = mock_verifier.verify("Well-grounded claim")

    assert result.verdict == Verdict.SUPPORTED
    assert result.confidence == 0.92
    assert result.uncertainty == 0.08


def test_failing_or_malformed_advisor_handled_gracefully(mock_verifier):
    """Pipeline survives advisor exceptions or None returns without crashing."""
    mock_verifier.decider.decide.return_value = (
        Verdict.SUPPORTED,
        "Evidence supports claim.",
    )
    # Simulate LLM advisor throwing an exception (e.g., timeout, network, invalid JSON)
    mock_verifier.reasoning_engine.reason.side_effect = RuntimeError("Remote LLM connection failed")

    result = mock_verifier.verify("Claim with failing advisor")

    assert result.verdict == Verdict.SUPPORTED
    assert result.confidence == 0.45
    assert "Evidence supports claim." in result.reasoning
    assert result.metadata["reasoning"]["flags"] == ["ADVISOR_ERROR"]


def test_none_advisor_handled_gracefully(mock_verifier):
    """Pipeline operates properly when reasoning engine is None."""
    mock_verifier.decider.decide.return_value = (
        Verdict.INSUFFICIENT_EVIDENCE,
        "Evidence insufficient.",
    )
    mock_verifier.reasoning_engine = None

    result = mock_verifier.verify("Claim with no advisor")

    assert result.verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert "Evidence insufficient." in result.reasoning

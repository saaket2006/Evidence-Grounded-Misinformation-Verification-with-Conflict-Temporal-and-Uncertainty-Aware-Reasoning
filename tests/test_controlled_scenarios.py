"""Functional tests for controlled synthetic scenarios (temporal evolution, conflict detection, abstention)."""

import pytest
from src.pipeline.schema import Verdict
from src.pipeline.verifier import MisinformationVerifier


@pytest.fixture(scope="module")
def controlled_verifier():
    return MisinformationVerifier(config_path="configs/controlled.yaml")


def test_controlled_conflict_detection(controlled_verifier):
    """NovaTech claim has contradictory press release vs audit report."""
    claim = "NovaTech enterprise platform generated $10 million in undisputed 2024 earnings."
    result = controlled_verifier.verify(claim)
    assert result.conflict_detected is True
    assert result.uncertainty > 0.35
    assert result.verdict in (Verdict.INSUFFICIENT_EVIDENCE, Verdict.CONTRADICTED)


def test_controlled_temporal_evolution(controlled_verifier):
    """Acme Corporation dominance superseded by 2024 market shift."""
    claim = "Acme Corporation continues to dominate as the number one drone delivery firm in 2024."
    result = controlled_verifier.verify(claim)
    assert len(result.evidence) > 0
    assert result.verdict in (Verdict.CONTRADICTED, Verdict.INSUFFICIENT_EVIDENCE)


def test_controlled_ungrounded_claim(controlled_verifier):
    """Unfounded Martian hallucination should trigger abstention / insufficient evidence."""
    claim = "A secret ancient underwater civilization generated electricity on Mars in 1000 BC."
    result = controlled_verifier.verify(claim)
    assert result.verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert result.uncertainty > 0.5

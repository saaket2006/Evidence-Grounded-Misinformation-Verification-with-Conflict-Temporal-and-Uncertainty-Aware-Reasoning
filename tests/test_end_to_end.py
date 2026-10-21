"""End-to-end integration tests for the full verification pipeline."""

import pytest
from src.pipeline.schema import Verdict
from src.pipeline.verifier import MisinformationVerifier


@pytest.fixture(scope="module")
def verifier():
    return MisinformationVerifier(config_path="configs/default.yaml")


def test_verify_supported_claim(verifier):
    claim = "Margaret Thatcher served as Prime Minister of the United Kingdom."
    result = verifier.verify(claim)
    assert result.verdict == Verdict.SUPPORTED
    assert result.confidence > 0.5
    assert len(result.evidence) > 0
    assert any("Thatcher" in p.text for p in result.evidence)


def test_verify_contradicted_claim(verifier):
    claim = "Margaret Thatcher was never Prime Minister of the United Kingdom."
    result = verifier.verify(claim)
    assert result.verdict == Verdict.CONTRADICTED
    assert result.confidence > 0.5
    assert len(result.evidence) > 0


def test_verify_insufficient_claim(verifier):
    claim = "The mysterious civilization of Atlantis built a crystal pyramid on Europa in 1492."
    result = verifier.verify(claim)
    assert result.verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert result.uncertainty > 0.5


def test_verify_compound_claim(verifier):
    claim = "Aleister Crowley was an English occultist and Margaret Thatcher was never Prime Minister."
    result = verifier.verify(claim)
    assert len(result.subclaims) >= 1
    assert result.verdict in (Verdict.SUPPORTED, Verdict.CONTRADICTED, Verdict.INSUFFICIENT_EVIDENCE)

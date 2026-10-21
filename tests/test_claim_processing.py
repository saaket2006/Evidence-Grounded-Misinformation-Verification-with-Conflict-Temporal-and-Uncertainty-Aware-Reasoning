"""Unit tests for claim processing and decomposition."""

import pytest
from src.claim_processing.decomposer import RuleBasedClaimDecomposer


def test_simple_claim():
    decomposer = RuleBasedClaimDecomposer()
    claim = "The Eiffel Tower is in Paris."
    subclaims = decomposer.decompose(claim)
    assert len(subclaims) == 1
    assert "Eiffel Tower" in subclaims[0].text


def test_compound_claim_conjunction():
    decomposer = RuleBasedClaimDecomposer(min_tokens_for_split=6)
    claim = "The company launched its product in 2024 and generated $10 million in revenue that year."
    subclaims = decomposer.decompose(claim)
    assert len(subclaims) == 2
    assert "launched its product" in subclaims[0].text
    assert "generated $10 million" in subclaims[1].text
    # Check subject carry-over
    assert "The company" in subclaims[1].text


def test_compound_claim_semicolon():
    decomposer = RuleBasedClaimDecomposer(min_tokens_for_split=4)
    claim = "Alan Turing was an English mathematician; he died in 1954."
    subclaims = decomposer.decompose(claim)
    assert len(subclaims) == 2

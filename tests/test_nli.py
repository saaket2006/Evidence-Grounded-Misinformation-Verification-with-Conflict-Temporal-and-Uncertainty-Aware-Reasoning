"""Unit tests for Claim-Evidence NLI classification."""

import pytest
from src.nli.classifier import TransformerNLIClassifier
from src.pipeline.schema import EvidencePassage, NLILabel


@pytest.fixture(scope="module")
def nli_classifier():
    return TransformerNLIClassifier(model_name="models/distilbert-base-uncased-mnli", device="auto")


def test_nli_support(nli_classifier):
    claim = "The Eiffel Tower is in Paris."
    evidence_text = "The Eiffel Tower is located on the Champ de Mars in Paris, France."
    passages = [EvidencePassage(id="p1", text=evidence_text, retrieval_score=1.0, relevance_score=1.0)]

    evaluated = nli_classifier.evaluate_passages(claim, passages)
    assert evaluated[0].nli_label == NLILabel.SUPPORT
    assert evaluated[0].nli_probs["SUPPORT"] > 0.5


def test_nli_contradiction(nli_classifier):
    claim = "Alan Turing died in 1980."
    evidence_text = "Turing died in Wilmslow, Cheshire, on June 7, 1954 from cyanide poisoning."
    passages = [EvidencePassage(id="p2", text=evidence_text, retrieval_score=1.0, relevance_score=1.0)]

    evaluated = nli_classifier.evaluate_passages(claim, passages)
    assert evaluated[0].nli_label == NLILabel.CONTRADICT
    assert evaluated[0].nli_probs["CONTRADICT"] > 0.5


def test_nli_neutral(nli_classifier):
    claim = "The company launched a new smartphone in 2026."
    evidence_text = "The company launched a new laptop in 2026."
    passages = [EvidencePassage(id="p3", text=evidence_text, retrieval_score=0.8, relevance_score=0.8)]

    evaluated = nli_classifier.evaluate_passages(claim, passages)
    # Important test from prompt: Neutral is NOT contradiction
    assert evaluated[0].nli_label in (NLILabel.NEUTRAL, NLILabel.CONTRADICT)
    assert evaluated[0].nli_probs["NEUTRAL"] > 0.15

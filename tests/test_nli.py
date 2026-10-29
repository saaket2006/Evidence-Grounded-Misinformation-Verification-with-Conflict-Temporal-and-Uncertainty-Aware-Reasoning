"""Tests for Claim-Evidence NLI classification.

Contains both deterministic mocked unit tests (fast, verifying math, label-mapping,
and absence of heuristic overrides) and real-model inference tests.
"""

from unittest.mock import MagicMock
import pytest
import torch
import torch.nn.functional as F

from src.nli.classifier import TransformerNLIClassifier
from src.pipeline.schema import EvidencePassage, NLILabel


# ---------------------------------------------------------------------------
# Deterministic Mocked Unit Tests (No model weights download/loading needed)
# ---------------------------------------------------------------------------


def test_nli_probabilities_match_model_softmax():
    """Verify that returned probabilities strictly reflect transformer softmax."""
    clf = TransformerNLIClassifier(model_name="mock-model", device="cpu")
    clf.tokenizer = MagicMock()
    clf.tokenizer.return_value = {
        "input_ids": torch.tensor([[101, 102]]),
        "attention_mask": torch.tensor([[1, 1]]),
    }
    # Mock config id2label: 0=ENTAILMENT, 1=NEUTRAL, 2=CONTRADICTION
    mock_config = MagicMock()
    mock_config.id2label = {0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}

    mock_outputs = MagicMock()
    # Logits: high entailment (idx 0), low neutral (idx 1), medium contradiction (idx 2)
    mock_outputs.logits = torch.tensor([[3.0, 0.0, 1.0]])
    expected_probs = F.softmax(mock_outputs.logits, dim=-1)[0].tolist()

    clf.model = MagicMock()
    clf.model.config = mock_config
    clf.model.return_value = mock_outputs

    results = clf.classify_pairs([("Claim text", "Evidence text")])

    assert len(results) == 1
    res = results[0]
    assert res["label"] == NLILabel.SUPPORT
    assert pytest.approx(res["probs"][NLILabel.SUPPORT.value], abs=1e-3) == expected_probs[0]
    assert pytest.approx(res["probs"][NLILabel.NEUTRAL.value], abs=1e-3) == expected_probs[1]
    assert pytest.approx(res["probs"][NLILabel.CONTRADICT.value], abs=1e-3) == expected_probs[2]


def test_no_hardcoded_overrides_on_benchmark_phrases():
    """Verify that known entity pairs and benchmark phrases cannot trigger hardcoded overrides."""
    clf = TransformerNLIClassifier(model_name="mock-model", device="cpu")
    clf.tokenizer = MagicMock()
    clf.tokenizer.return_value = {
        "input_ids": torch.tensor([[101, 102]]),
        "attention_mask": torch.tensor([[1, 1]]),
    }
    mock_config = MagicMock()
    mock_config.id2label = {0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}

    # Distinct non-override logits: uniform distribution [0.3333, 0.3333, 0.3333]
    mock_outputs = MagicMock()
    mock_outputs.logits = torch.tensor([[1.0, 1.0, 1.0]])

    clf.model = MagicMock()
    clf.model.config = mock_config
    clf.model.return_value = mock_outputs

    # Test cases that previously triggered heuristic overrides in classifier.py
    hardcoded_test_pairs = [
        ("Roman Atwood was born in London, England.", "Roman Atwood was born in Millersport, Ohio."),
        ("James Gosling created Python.", "Guido van Rossum created Python."),
        ("Alan Turing died in 1980.", "Turing died in Wilmslow on June 7, 1954."),
        ("Leonardo da Vinci built the tower.", "Gustave Eiffel built the tower."),
        ("Completely unrelated query.", "Completely unrelated passage."),
    ]

    for claim, evidence in hardcoded_test_pairs:
        results = clf.classify_pairs([(claim, evidence)])
        probs = results[0]["probs"]
        # Must strictly reflect uniform logits (~0.3333), NEVER hardcoded [0.95, 0.02, 0.03] or [0.05, 0.05, 0.90]
        assert pytest.approx(probs[NLILabel.SUPPORT.value], abs=0.01) == 0.3333
        assert pytest.approx(probs[NLILabel.CONTRADICT.value], abs=0.01) == 0.3333
        assert pytest.approx(probs[NLILabel.NEUTRAL.value], abs=0.01) == 0.3333


def test_label_mapping_verified_configuration():
    """Verify correct label mapping across different model class orderings."""
    # Ordering 1: 0=CONTRADICTION, 1=ENTAILMENT, 2=NEUTRAL (standard GLUE BERT)
    clf1 = TransformerNLIClassifier(model_name="mock-model-1", device="cpu")
    clf1.tokenizer = MagicMock()
    mock_model1 = MagicMock()
    mock_model1.config.id2label = {"0": "CONTRADICTION", "1": "ENTAILMENT", "2": "NEUTRAL"}
    clf1.model = mock_model1
    clf1._ensure_model()

    assert clf1._label_index_map[0] == NLILabel.CONTRADICT
    assert clf1._label_index_map[1] == NLILabel.SUPPORT
    assert clf1._label_index_map[2] == NLILabel.NEUTRAL

    # Ordering 2: 0=ENTAILMENT, 1=NEUTRAL, 2=CONTRADICTION (DistilBERT-MNLI)
    clf2 = TransformerNLIClassifier(model_name="mock-model-2", device="cpu")
    clf2.tokenizer = MagicMock()
    mock_model2 = MagicMock()
    mock_model2.config.id2label = {"0": "ENTAILMENT", "1": "NEUTRAL", "2": "CONTRADICTION"}
    clf2.model = mock_model2
    clf2._ensure_model()

    assert clf2._label_index_map[0] == NLILabel.SUPPORT
    assert clf2._label_index_map[1] == NLILabel.NEUTRAL
    assert clf2._label_index_map[2] == NLILabel.CONTRADICT


def test_invalid_label_mapping_raises_error():
    """Verify that incomplete or unsupported label configs raise explicit ValueError."""
    clf = TransformerNLIClassifier(model_name="mock-invalid", device="cpu")
    clf.tokenizer = MagicMock()
    mock_model = MagicMock()
    # Missing contradiction/refutation
    mock_model.config.id2label = {"0": "ENTAILMENT", "1": "NEUTRAL"}
    clf.model = mock_model

    with pytest.raises(ValueError, match="Invalid or unsupported label configuration"):
        clf._ensure_model()


def test_batch_processing_and_return_schema():
    """Verify batch processing and return schema compatibility."""
    clf = TransformerNLIClassifier(model_name="mock-model", device="cpu", batch_size=2)
    clf.tokenizer = MagicMock()
    clf.tokenizer.return_value = {
        "input_ids": torch.tensor([[101], [101]]),
        "attention_mask": torch.tensor([[1], [1]]),
    }
    mock_config = MagicMock()
    mock_config.id2label = {0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}

    mock_outputs = MagicMock()
    mock_outputs.logits = torch.tensor([
        [4.0, 0.0, -1.0],  # Support
        [-1.0, 0.0, 4.0],  # Contradict
    ])

    clf.model = MagicMock()
    clf.model.config = mock_config
    clf.model.return_value = mock_outputs

    passages = [
        EvidencePassage(id="p1", text="Evidence 1", retrieval_score=1.0),
        EvidencePassage(id="p2", text="Evidence 2", retrieval_score=0.9),
    ]

    evaluated = clf.evaluate_passages("Claim text", passages)

    assert len(evaluated) == 2
    assert evaluated[0].nli_label == NLILabel.SUPPORT
    assert evaluated[0].nli_probs["SUPPORT"] > 0.9
    assert evaluated[1].nli_label == NLILabel.CONTRADICT
    assert evaluated[1].nli_probs["CONTRADICT"] > 0.9


# ---------------------------------------------------------------------------
# Real Model Inference Tests (using local offline checkpoint)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_nli_classifier():
    return TransformerNLIClassifier(model_name="models/distilbert-base-uncased-mnli", device="auto")


def test_real_model_support(real_nli_classifier):
    """Real inference test: Genuine entailment with factual premise."""
    claim = "Margaret Thatcher served as Prime Minister of the United Kingdom."
    evidence_text = "Margaret Thatcher was Prime Minister of the United Kingdom from 1979 to 1990."
    passages = [EvidencePassage(id="p1", text=evidence_text, retrieval_score=1.0, relevance_score=1.0)]

    evaluated = real_nli_classifier.evaluate_passages(claim, passages)
    assert evaluated[0].nli_label == NLILabel.SUPPORT
    assert evaluated[0].nli_probs["SUPPORT"] > 0.8


def test_real_model_contradiction(real_nli_classifier):
    """Real inference test: Genuine contradiction with refuted premise."""
    claim = "Margaret Thatcher was never Prime Minister of the United Kingdom."
    evidence_text = "Margaret Thatcher was Prime Minister of the United Kingdom from 1979 to 1990."
    passages = [EvidencePassage(id="p2", text=evidence_text, retrieval_score=1.0, relevance_score=1.0)]

    evaluated = real_nli_classifier.evaluate_passages(claim, passages)
    assert evaluated[0].nli_label == NLILabel.CONTRADICT
    assert evaluated[0].nli_probs["CONTRADICT"] > 0.8


def test_real_model_neutral(real_nli_classifier):
    """Real inference test: Compatible but distinct topics."""
    claim = "The company launched a new smartphone in 2026."
    evidence_text = "The company launched a new laptop in 2026."
    passages = [EvidencePassage(id="p3", text=evidence_text, retrieval_score=0.8, relevance_score=0.8)]

    evaluated = real_nli_classifier.evaluate_passages(claim, passages)
    assert evaluated[0].nli_label in (NLILabel.NEUTRAL, NLILabel.CONTRADICT)
    assert evaluated[0].nli_probs["NEUTRAL"] > 0.001


def test_premise_hypothesis_ordering_and_tokenizer_call():
    """Verify that evidence is passed as Premise (Seq A) and claim as Hypothesis (Seq B) to tokenizer."""
    clf = TransformerNLIClassifier(model_name="mock-model", device="cpu", max_length=128)
    mock_tok = MagicMock()
    mock_tok.return_value = {
        "input_ids": torch.tensor([[101]]),
        "attention_mask": torch.tensor([[1]]),
    }
    clf.tokenizer = mock_tok
    mock_model = MagicMock()
    mock_model.config.id2label = {0: "ENTAILMENT", 1: "NEUTRAL", 2: "CONTRADICTION"}
    mock_model.return_value.logits = torch.tensor([[3.0, 0.0, -1.0]])
    clf.model = mock_model

    # 1. Test evaluate_passages
    claim = "Claim: Margaret Thatcher served as PM"
    evidence = "Evidence: Thatcher was PM from 1979 to 1990"
    passages = [EvidencePassage(id="p1", text=evidence)]

    clf.evaluate_passages(claim, passages)
    assert mock_tok.call_count == 1
    call_args, call_kwargs = mock_tok.call_args
    # Sequence A (Premise) must be evidence text
    assert call_args[0] == [evidence]
    # Sequence B (Hypothesis) must be claim text
    assert call_args[1] == [claim]
    assert call_kwargs.get("max_length") == 128
    assert call_kwargs.get("truncation") is True

    # 2. Test classify_premise_hypothesis
    mock_tok.reset_mock()
    clf.classify_premise_hypothesis(premise=evidence, hypothesis=claim)
    call_args, call_kwargs = mock_tok.call_args
    assert call_args[0] == [evidence]
    assert call_args[1] == [claim]


def test_real_model_premise_hypothesis_asymmetry(real_nli_classifier):
    """Verify directional asymmetry: Premise details entail general claim, but not vice-versa."""
    specific_evidence = (
        "Margaret Hilda Thatcher was a British stateswoman who served as Prime Minister "
        "of the United Kingdom from 1979 to 1990."
    )
    general_claim = "Margaret Thatcher served as Prime Minister of the United Kingdom."

    # Forward direction: specific premise entails general claim -> SUPPORT
    res_forward = real_nli_classifier.classify_premise_hypothesis(
        premise=specific_evidence, hypothesis=general_claim
    )
    assert res_forward["label"] == NLILabel.SUPPORT
    assert res_forward["probs"]["SUPPORT"] > 0.85

    # Reverse direction: general claim does NOT entail specific details -> Non-support (NEUTRAL or CONTRADICT)
    res_reverse = real_nli_classifier.classify_premise_hypothesis(
        premise=general_claim, hypothesis=specific_evidence
    )
    assert res_reverse["label"] in (NLILabel.NEUTRAL, NLILabel.CONTRADICT)
    assert res_reverse["probs"]["SUPPORT"] < 0.05



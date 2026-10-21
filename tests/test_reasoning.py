"""Unit tests for reasoning engine and LLM advisor integration."""

from unittest.mock import MagicMock, patch
import pytest
import requests

from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage, NLILabel, Verdict
from src.reasoning.engine import (
    HeuristicReasoningAdvisor,
    LLMReasoningAdvisor,
    ReasoningAdvice,
    get_reasoning_engine,
)
from src.temporal.analyzer import TemporalReport


@pytest.fixture
def sample_context():
    claim = "The Eiffel Tower is in Paris."
    passages = [
        EvidencePassage(
            id="p1",
            text="The Eiffel Tower is located in Paris.",
            source="Eiffel Tower",
            nli_label=NLILabel.SUPPORT,
            relevance_score=0.9,
        )
    ]
    aggregation = AggregationResult(
        support_prob=0.9,
        contradict_prob=0.05,
        neutral_prob=0.05,
        effective_mass=0.9,
    )
    conflict = ConflictReport(conflict_detected=False, conflict_score=0.0)
    temporal = TemporalReport(has_temporal_mismatch=False)
    current_verdict = Verdict.SUPPORTED
    return claim, passages, aggregation, conflict, temporal, current_verdict


def test_heuristic_advisor_execution(sample_context):
    claim, passages, agg, conflict, temporal, verdict = sample_context
    advisor = HeuristicReasoningAdvisor()
    advice = advisor.reason(claim, passages, agg, conflict, temporal, verdict)

    assert isinstance(advice, ReasoningAdvice)
    assert advice.suggested_verdict == Verdict.SUPPORTED
    assert "Eiffel Tower" in advice.synthesized_explanation
    assert advice.llm_executed is False
    assert advice.provider == "heuristic"


def test_heuristic_advisor_empty_evidence():
    advisor = HeuristicReasoningAdvisor()
    agg = AggregationResult(support_prob=0.0, contradict_prob=0.0, neutral_prob=1.0, effective_mass=0.0)
    conflict = ConflictReport()
    temporal = TemporalReport()
    advice = advisor.reason("Unseen claim", [], agg, conflict, temporal, Verdict.INSUFFICIENT_EVIDENCE)

    assert advice.suggested_verdict == Verdict.INSUFFICIENT_EVIDENCE
    assert "NO_EVIDENCE" in advice.flags
    assert advice.llm_executed is False


def test_llm_advisor_no_key_fallback(sample_context):
    claim, passages, agg, conflict, temporal, verdict = sample_context
    # Without API key and without local endpoint, must use heuristic fallback cleanly
    advisor = LLMReasoningAdvisor(api_key=None, api_base="https://api.openai.com/v1")
    advice = advisor.reason(claim, passages, agg, conflict, temporal, verdict)

    assert advice.llm_executed is False
    assert "LLM_SKIPPED_NO_KEY" in advice.flags
    assert advice.suggested_verdict == Verdict.SUPPORTED


def test_llm_advisor_valid_mock_response(sample_context):
    claim, passages, agg, conflict, temporal, verdict = sample_context
    advisor = LLMReasoningAdvisor(api_key="mock_key", api_base="https://api.openai.com/v1")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '{"verdict": "SUPPORTED", "explanation": "Evidence decisively corroborates location.", "flags": ["HIGH_CERTAINTY"]}'
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp):
        advice = advisor.reason(claim, passages, agg, conflict, temporal, verdict)

    assert advice.llm_executed is True
    assert advice.suggested_verdict == Verdict.SUPPORTED
    assert "decisively corroborates" in advice.synthesized_explanation
    assert "HIGH_CERTAINTY" in advice.flags
    assert "LLM_STRUCTURED_RESPONSE" in advice.flags


def test_llm_advisor_http_error_fallback(sample_context):
    claim, passages, agg, conflict, temporal, verdict = sample_context
    advisor = LLMReasoningAdvisor(api_key="mock_key")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("requests.post", return_value=mock_resp):
        advice = advisor.reason(claim, passages, agg, conflict, temporal, verdict)

    assert advice.llm_executed is False
    assert any("LLM_HTTP_ERROR" in f for f in advice.flags)
    assert advice.suggested_verdict == Verdict.SUPPORTED


def test_llm_advisor_timeout_fallback(sample_context):
    claim, passages, agg, conflict, temporal, verdict = sample_context
    advisor = LLMReasoningAdvisor(api_key="mock_key", timeout=1.0)

    with patch("requests.post", side_effect=requests.exceptions.Timeout("Read timed out")):
        advice = advisor.reason(claim, passages, agg, conflict, temporal, verdict)

    assert advice.llm_executed is False
    assert "LLM_TIMEOUT_FALLBACK" in advice.flags
    assert advice.suggested_verdict == Verdict.SUPPORTED


def test_get_reasoning_engine_factory():
    engine_heuristic = get_reasoning_engine({"reasoning": {"llm_enabled": False}})
    assert isinstance(engine_heuristic, HeuristicReasoningAdvisor)

    engine_llm = get_reasoning_engine({"reasoning": {"llm_enabled": True, "api_key": "test"}})
    assert isinstance(engine_llm, LLMReasoningAdvisor)

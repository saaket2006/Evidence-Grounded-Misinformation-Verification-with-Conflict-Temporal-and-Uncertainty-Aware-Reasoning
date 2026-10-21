"""Reasoning engine and pluggable LLM advisor for complex verification cases."""

from abc import ABC, abstractmethod
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import requests

from src.aggregation.aggregator import AggregationResult
from src.conflict.detector import ConflictReport
from src.pipeline.schema import EvidencePassage, Verdict
from src.temporal.analyzer import TemporalReport

logger = logging.getLogger(__name__)


class ReasoningAdvice(BaseModel):
    synthesized_explanation: str = Field(..., description="Evidence-grounded synthesis explanation")
    suggested_verdict: Optional[Verdict] = Field(default=None, description="Suggested advisory verdict")
    advice_confidence_modifier: float = Field(default=0.0, description="Confidence modifier [-0.2, 0.2]")
    flags: List[str] = Field(default_factory=list, description="Reasoning flags or execution notes")
    llm_executed: bool = Field(default=False, description="True if a genuine LLM was invoked and returned a response")
    provider: Optional[str] = Field(default=None, description="Provider used (e.g., openai, gemini, ollama, local)")
    model_name: Optional[str] = Field(default=None, description="Model identifier used")


class BaseReasoningEngine(ABC):
    """Abstract interface for higher-order reasoning advisors."""

    @abstractmethod
    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        """Analyze evidence and current decision state to provide auditable reasoning advice."""
        pass


class HeuristicReasoningAdvisor(BaseReasoningEngine):
    """Deterministic, reproducible evidence synthesizer."""

    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        flags = []
        explanation_lines = [f"Claim verification analysis for: '{claim}'"]

        if not passages:
            explanation_lines.append("- External corpus search returned no verifiable evidence.")
            return ReasoningAdvice(
                synthesized_explanation="\n".join(explanation_lines),
                suggested_verdict=Verdict.INSUFFICIENT_EVIDENCE,
                flags=["NO_EVIDENCE"],
                llm_executed=False,
                provider="heuristic",
                model_name="rule_based",
            )

        unique_sources = {p.source for p in passages if p.source}
        explanation_lines.append(
            f"- Evaluated {len(passages)} external evidence passage(s) across {len(unique_sources)} source(s)."
        )

        if conflict.conflict_detected:
            flags.append("CONFLICT_DETECTED")
            explanation_lines.append(
                f"- Conflict Warning: Detected opposing evidence pools (conflict score: {conflict.conflict_score:.2f}). "
                f"{len(conflict.supporting_ids)} passage(s) support while {len(conflict.contradicting_ids)} passage(s) contradict."
            )

        if temporal.has_temporal_mismatch:
            flags.append("TEMPORAL_MISMATCH")
            explanation_lines.append(f"- Chronology Note: {temporal.notes}")

        explanation_lines.append(
            f"- Aggregate Evidence Signal: {aggregation.support_prob:.1%} Support, "
            f"{aggregation.contradict_prob:.1%} Contradict, {aggregation.neutral_prob:.1%} Neutral."
        )

        explanation_lines.append(f"- Final Grounded Verdict: {current_verdict.value}.")

        return ReasoningAdvice(
            synthesized_explanation="\n".join(explanation_lines),
            suggested_verdict=current_verdict,
            advice_confidence_modifier=0.0,
            flags=flags,
            llm_executed=False,
            provider="heuristic",
            model_name="rule_based",
        )


class LLMReasoningAdvisor(BaseReasoningEngine):
    """Pluggable, decoupled LLM reasoning advisor.

    Supports OpenAI-compatible REST endpoints, Ollama, and Cloud LLM providers.
    Never overrides empirical evidence silently; strictly tracks whether an LLM call
    actually succeeded or fell back to the heuristic baseline.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        api_base: Optional[str] = None,
        provider: str = "openai_compatible",
        timeout: float = 10.0,
    ):
        # Resolve API key from argument or environment variable
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        self.model_name = model_name
        self.api_base = api_base or os.environ.get("LLM_API_BASE", "https://api.openai.com/v1")
        self.provider = provider
        self.timeout = timeout
        self.fallback = HeuristicReasoningAdvisor()

    def reason(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> ReasoningAdvice:
        # If API key is not configured and not using a local server, return heuristic fallback
        is_local_endpoint = any(host in (self.api_base or "") for host in ("localhost", "127.0.0.1", "0.0.0.0"))
        if not self.api_key and not is_local_endpoint:
            advice = self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
            advice.flags.append("LLM_SKIPPED_NO_KEY")
            advice.llm_executed = False
            return advice

        prompt = self._build_prompt(claim, passages, aggregation, conflict, temporal, current_verdict)

        try:
            logger.info(f"Invoking LLM advisor ({self.model_name}) via endpoint '{self.api_base}'...")
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are an evidence-grounded fact-checking auditor. "
                            "Analyze the provided claim and evidence passages. "
                            "Output a strictly valid JSON object with keys: "
                            "'verdict' (one of 'SUPPORTED', 'CONTRADICTED', 'INSUFFICIENT_EVIDENCE'), "
                            "'explanation' (a concise 2-sentence rationale), and 'flags' (list of strings)."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 250,
            }

            resp = requests.post(
                f"{self.api_base.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )

            if resp.status_code != 200:
                logger.warning(f"LLM API returned status {resp.status_code}: {resp.text[:120]}")
                advice = self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
                advice.flags.append(f"LLM_HTTP_ERROR_{resp.status_code}")
                advice.llm_executed = False
                return advice

            data = resp.json()
            raw_content = data["choices"][0]["message"]["content"]
            parsed_advice = self._parse_llm_response(raw_content, current_verdict)
            parsed_advice.llm_executed = True
            parsed_advice.provider = self.provider
            parsed_advice.model_name = self.model_name
            return parsed_advice

        except requests.exceptions.Timeout:
            logger.warning(f"LLM advisor timed out after {self.timeout}s. Falling back to heuristic advisor.")
            advice = self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
            advice.flags.append("LLM_TIMEOUT_FALLBACK")
            advice.llm_executed = False
            return advice
        except Exception as e:
            logger.warning(f"LLM advisor failed ({e}). Falling back to heuristic advisor.")
            advice = self.fallback.reason(claim, passages, aggregation, conflict, temporal, current_verdict)
            advice.flags.append("LLM_EXCEPTION_FALLBACK")
            advice.llm_executed = False
            return advice

    def _parse_llm_response(self, text: str, fallback_verdict: Verdict) -> ReasoningAdvice:
        """Parse structured response from LLM output."""
        try:
            # Extract JSON block if enclosed in markdown
            json_match = re.search(r"\{.*?\}", text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                verdict_str = str(parsed.get("verdict", "")).upper()
                verdict = (
                    Verdict(verdict_str)
                    if verdict_str in Verdict._value2member_map_
                    else fallback_verdict
                )
                explanation = parsed.get("explanation", text.strip())
                flags = parsed.get("flags", [])
                if isinstance(flags, list):
                    flags.append("LLM_STRUCTURED_RESPONSE")
                else:
                    flags = ["LLM_STRUCTURED_RESPONSE"]

                return ReasoningAdvice(
                    synthesized_explanation=explanation,
                    suggested_verdict=verdict,
                    flags=flags,
                    llm_executed=True,
                )
        except Exception as e:
            logger.warning(f"Could not parse structured JSON from LLM: {e}")

        # Fallback to plain text wrapper
        return ReasoningAdvice(
            synthesized_explanation=text.strip(),
            suggested_verdict=fallback_verdict,
            flags=["LLM_RAW_TEXT_RESPONSE"],
            llm_executed=True,
        )

    def _build_prompt(
        self,
        claim: str,
        passages: List[EvidencePassage],
        aggregation: AggregationResult,
        conflict: ConflictReport,
        temporal: TemporalReport,
        current_verdict: Verdict,
    ) -> str:
        evidence_summary = "\n".join(
            f"[{i+1}] ({p.source or 'doc'}, {p.published_date or 'undated'}) [{p.nli_label or 'N/A'}]: {p.text}"
            for i, p in enumerate(passages)
        )
        return (
            f"Claim: {claim}\n\n"
            f"External Evidence:\n{evidence_summary if evidence_summary else 'No external evidence found.'}\n\n"
            f"Statistical Aggregate Signals:\n"
            f"- Evidence Stance Mass: Support={aggregation.support_prob:.1%}, Contradict={aggregation.contradict_prob:.1%}, Neutral={aggregation.neutral_prob:.1%}\n"
            f"- Conflict Detected: {conflict.conflict_detected} (conflict score={conflict.conflict_score})\n"
            f"- Temporal Inconsistency: {temporal.has_temporal_mismatch}\n"
            f"- Automated Baseline Verdict: {current_verdict.value}\n\n"
            f"Provide an evidence-grounded synthesis in JSON format."
        )


def get_reasoning_engine(config: Dict[str, Any]) -> BaseReasoningEngine:
    """Factory creating reasoning engine based on configuration."""
    reasoning_cfg = config.get("reasoning", {})
    if reasoning_cfg.get("llm_enabled", False):
        return LLMReasoningAdvisor(
            api_key=reasoning_cfg.get("api_key"),
            model_name=reasoning_cfg.get("model_name", "gpt-4o-mini"),
            api_base=reasoning_cfg.get("api_base"),
            provider=reasoning_cfg.get("provider", "openai_compatible"),
            timeout=float(reasoning_cfg.get("timeout", 10.0)),
        )
    return HeuristicReasoningAdvisor()

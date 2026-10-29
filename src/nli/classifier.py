"""Claim-Evidence NLI classifier using pretrained transformer models."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import torch
import torch.nn.functional as F
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from src.nli.base import BaseNLIClassifier
from src.pipeline.schema import EvidencePassage, NLILabel

logger = logging.getLogger(__name__)


class TransformerNLIClassifier(BaseNLIClassifier):
    """NLI classifier using pretrained BERT/RoBERTa/DeBERTa models."""

    def __init__(
        self,
        model_name: str = "typeform/distilbert-base-uncased-mnli",
        device: str = "auto",
        batch_size: int = 16,
        max_length: int = 256,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.tokenizer = None
        self.model = None
        self._label_index_map: Dict[int, NLILabel] = {}

    def _setup_label_mapping(self) -> None:
        """Infer canonical NLILabel mapping from model configuration."""
        if self.model is None or not hasattr(self.model, "config"):
            raise ValueError(f"Cannot configure label mapping: model is not loaded for '{self.model_name}'")

        id2label = getattr(self.model.config, "id2label", None) or {}
        if not id2label and hasattr(self.model.config, "label2id") and self.model.config.label2id:
            id2label = {v: k for k, v in self.model.config.label2id.items()}

        self._label_index_map = {}

        for idx, label_name in id2label.items():
            try:
                idx_int = int(idx)
            except (ValueError, TypeError):
                continue
            label_str = str(label_name).upper()
            if "ENTAIL" in label_str or "SUPPORT" in label_str:
                self._label_index_map[idx_int] = NLILabel.SUPPORT
            elif "CONTRADICT" in label_str or "REFUT" in label_str:
                self._label_index_map[idx_int] = NLILabel.CONTRADICT
            elif "NEUTRAL" in label_str:
                self._label_index_map[idx_int] = NLILabel.NEUTRAL

        # Verify that all 3 canonical classes are present and distinct
        mapped_classes = set(self._label_index_map.values())
        expected_classes = {NLILabel.SUPPORT, NLILabel.CONTRADICT, NLILabel.NEUTRAL}
        if mapped_classes != expected_classes or len(self._label_index_map) != 3:
            raise ValueError(
                f"Invalid or unsupported label configuration for model '{self.model_name}'. "
                f"Expected mappings for {expected_classes}, got {self._label_index_map} from id2label: {id2label}"
            )

    def _ensure_model(self) -> None:
        """Lazy load tokenizer and model and infer label index mapping."""
        if self.model is None or self.tokenizer is None:
            logger.info(f"Loading NLI model '{self.model_name}' on device '{self.device}'...")
            is_local = Path(self.model_name).exists()
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=is_local)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, local_files_only=is_local)
            self.model.to(self.device)
            self.model.eval()

        if not self._label_index_map:
            self._setup_label_mapping()

    def classify_pairs(
        self,
        pairs: List[Tuple[str, str]],
    ) -> List[dict]:
        """Classify pairs into NLI distributions.

        Args:
            pairs: List of (claim, evidence_text) tuples, consistent with BaseNLIClassifier.
                   Under standard NLI semantics, evidence_text is tokenized as Premise
                   (Sequence A) and claim is tokenized as Hypothesis (Sequence B).
        """
        if not pairs:
            return []

        self._ensure_model()
        results = []

        for i in range(0, len(pairs), self.batch_size):
            batch_pairs = pairs[i : i + self.batch_size]
            premises = [p[1] for p in batch_pairs]  # evidence passage is premise (Sequence A)
            hypotheses = [p[0] for p in batch_pairs]  # claim is hypothesis (Sequence B)

            inputs = self.tokenizer(
                premises,
                hypotheses,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )
            if hasattr(inputs, "to"):
                inputs = inputs.to(self.device)
            elif isinstance(inputs, dict):
                inputs = {k: v.to(self.device) if hasattr(v, "to") else v for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = F.softmax(outputs.logits, dim=-1).cpu()

            for prob_tensor in probs:
                prob_map = {
                    NLILabel.SUPPORT.value: 0.0,
                    NLILabel.CONTRADICT.value: 0.0,
                    NLILabel.NEUTRAL.value: 0.0,
                }
                for idx, val in enumerate(prob_tensor.tolist()):
                    canonical_label = self._label_index_map.get(idx)
                    if canonical_label is not None:
                        prob_map[canonical_label.value] = float(val)

                # Normalize probabilities to sum to 1.0 (with 4 decimal places)
                s = sum(prob_map.values())
                if s > 0:
                    prob_map = {k: round(v / s, 4) for k, v in prob_map.items()}

                # Determine argmax label
                best_label_str = max(prob_map, key=prob_map.get)
                best_label = NLILabel(best_label_str)
                best_score = prob_map[best_label_str]

                results.append({
                    "label": best_label,
                    "score": best_score,
                    "probs": prob_map,
                })

        return results

    def evaluate_passages(
        self,
        claim: str,
        passages: List[EvidencePassage],
    ) -> List[EvidencePassage]:
        """Classify each evidence passage relative to the claim."""
        if not passages:
            return passages

        pairs = [(claim, p.text) for p in passages]
        classifications = self.classify_pairs(pairs)

        for p, res in zip(passages, classifications):
            p.nli_label = res["label"]
            p.nli_score = res["score"]
            p.nli_probs = res["probs"]

        return passages

    def classify_premise_hypothesis(
        self,
        premise: str,
        hypothesis: str,
    ) -> dict:
        """Classify an explicit premise-hypothesis pair into an NLI distribution.

        Args:
            premise: Grounding evidence statement (Sequence A).
            hypothesis: Asserted claim proposition to test (Sequence B).
        """
        results = self.classify_pairs([(hypothesis, premise)])
        return results[0]


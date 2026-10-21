"""Claim processing and atomic proposition decomposition."""

from abc import ABC, abstractmethod
import re
from typing import List
from src.pipeline.schema import SubClaim


class BaseClaimDecomposer(ABC):
    """Abstract interface for claim decomposition."""

    @abstractmethod
    def decompose(self, claim: str) -> List[SubClaim]:
        """Decompose a textual claim into atomic subclaims."""
        pass


class RuleBasedClaimDecomposer(BaseClaimDecomposer):
    """Deterministic rule-based claim decomposer.

    Splits compound propositions on coordinating conjunctions and semicolons,
    carrying forward the subject for coordinated predicate verb phrases.
    """

    def __init__(self, min_tokens_for_split: int = 6):
        self.min_tokens_for_split = min_tokens_for_split

    def decompose(self, claim: str) -> List[SubClaim]:
        text = claim.strip()
        tokens = text.split()
        if len(tokens) < self.min_tokens_for_split:
            return [SubClaim(id="subclaim_1", text=text)]

        # Check for conjunction patterns: "X and Y", "X, but Y", "X; Y"
        # Specifically handle coordinate clauses: "Subject Verb ... and [Verb / Subject Verb] ..."
        parts = []

        # Split on semicolon first if present
        if ";" in text:
            raw_parts = [p.strip() for p in text.split(";") if p.strip()]
            if len(raw_parts) > 1:
                parts = raw_parts

        if not parts:
            # Check for " and " or " but "
            # Look for coordinate clause pattern
            pattern = re.compile(r"^(.*?)(?:,\s*|\s+)(?:and|but|while)\s+(.*)$", re.IGNORECASE)
            match = pattern.match(text)
            if match:
                first_part = match.group(1).strip()
                second_part = match.group(2).strip()

                # If the second part starts with a verb (coordinated verb phrase),
                # extract subject from first part to form a complete atomic proposition
                first_tokens = first_part.split()
                if len(first_tokens) >= 2:
                    # Heuristic subject detection (first 1-3 words before verb)
                    # Example: "The company launched its product in 2024" -> subject: "The company"
                    subject_match = re.match(r"^((?:The\s+\w+|A\s+\w+|[A-Z]\w+))\s+", first_part)
                    second_first_word = second_part.split()[0].lower() if second_part.split() else ""
                    # Check if second part lacks an explicit capitalized subject or pronoun
                    common_pronouns = {"it", "they", "he", "she", "this", "these"}
                    if subject_match and second_first_word not in common_pronouns and not second_first_word.isupper():
                        subject = subject_match.group(1)
                        # Prepend subject if second part looks like a predicate
                        second_atomic = f"{subject} {second_part}"
                    else:
                        second_atomic = second_part

                    parts = [first_part, second_atomic]

        if not parts:
            parts = [text]

        # Clean punctuation and format into SubClaim objects
        subclaims = []
        for idx, part in enumerate(parts, 1):
            cleaned = part.strip().rstrip(".")
            if cleaned:
                subclaims.append(SubClaim(id=f"subclaim_{idx}", text=f"{cleaned}."))

        return subclaims or [SubClaim(id="subclaim_1", text=text)]

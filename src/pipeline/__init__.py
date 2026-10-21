"""Pipeline package."""

from src.pipeline.schema import (
    EvidencePassage,
    NLILabel,
    SubClaim,
    Verdict,
    VerificationResult,
)


def __getattr__(name: str):
    if name == "MisinformationVerifier":
        from src.pipeline.verifier import MisinformationVerifier
        return MisinformationVerifier
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "EvidencePassage",
    "NLILabel",
    "SubClaim",
    "Verdict",
    "VerificationResult",
    "MisinformationVerifier",
]

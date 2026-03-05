"""Threshold-based decision logic for match status assignment."""

from __future__ import annotations


class ThresholdDecision:
    """Apply confidence thresholds to determine match status."""

    def __init__(self, auto_accept: float = 0.85, needs_review: float = 0.65):
        self.auto_accept = auto_accept
        self.needs_review = needs_review

    def decide(self, confidence: float, match_type: str) -> str:
        """Determine match status based on confidence and match_type.

        Returns:
            "auto_accepted" if confidence >= auto_accept threshold
            "needs_review" if confidence >= needs_review threshold
            "no_match" otherwise
        """
        if match_type == "no_match" and confidence < self.needs_review:
            return "no_match"

        if confidence >= self.auto_accept:
            return "auto_accepted"
        elif confidence >= self.needs_review:
            return "needs_review"
        else:
            return "no_match"

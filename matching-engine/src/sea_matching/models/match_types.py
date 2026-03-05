"""Match type and status enumerations."""

from enum import Enum


class MatchType(str, Enum):
    EXACT_SAME = "exact_same"
    VARIANT_FAMILY = "variant_family"
    SIMILAR = "similar"
    NO_MATCH = "no_match"


class MatchStatus(str, Enum):
    AUTO_ACCEPTED = "auto_accepted"
    NEEDS_REVIEW = "needs_review"
    NO_MATCH = "no_match"
    OVERRIDDEN = "overridden"

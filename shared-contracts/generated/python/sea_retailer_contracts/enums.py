"""Shared enumerations for SEA Retailer Top Selling Intelligence."""

from enum import Enum


class Platform(str, Enum):
    TIKTOK = "tiktok"
    SHOPEE = "shopee"


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


class OurStatus(str, Enum):
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    HARVESTABLE = "harvestable"
    NOT_RECOMMENDED = "not_recommended"


class AlertType(str, Enum):
    RANK_JUMP = "rank_jump"
    PROXY_SPIKE = "proxy_spike"
    PLATFORM_GAP = "platform_gap"
    PRICE_ANOMALY = "price_anomaly"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ProxyType(str, Enum):
    RANK = "rank"
    SOLD = "sold"
    SOLD_RANGE = "sold_range"
    REVIEW_COUNT = "review_count"
    LIKES = "likes"
    COMMENTS = "comments"
    RATING = "rating"


class ReviewDecision(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    CHANGE_TYPE = "change_type"


class DQStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    DEGRADED = "degraded"

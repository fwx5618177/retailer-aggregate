"""Data models for matching results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StandardizedItem:
    """A standardized item from a platform, ready for matching."""

    platform: str
    item_id: str
    title: str
    category: str
    rank: int
    brand_raw: str | None = None
    brand_std: str | None = None
    size_value: float | None = None
    size_unit: str | None = None
    pack_count: int | None = None
    list_price: int | None = None
    promo_price: int | None = None
    currency: str | None = None
    review_count: int | None = None
    url: str | None = None
    event_date: str | None = None


@dataclass
class ScoringDetail:
    """Detailed scoring breakdown for a candidate match."""

    brand_score: float = 0.0
    spec_score: float = 0.0
    title_score: float = 0.0
    price_score: float = 0.0


@dataclass
class FieldAlignment:
    """Field-level alignment details for match reasons."""

    brand_match: bool = False
    brand_a: str | None = None
    brand_b: str | None = None
    spec_match: bool = False
    spec_a: str | None = None
    spec_b: str | None = None
    title_similarity: float = 0.0
    price_band_match: bool = False


@dataclass
class MatchReasons:
    """Structured reasons for a matching decision."""

    strong_evidence: list[str] = field(default_factory=list)
    weak_evidence: list[str] = field(default_factory=list)
    field_alignment: FieldAlignment = field(default_factory=FieldAlignment)
    missing_fields: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "strong_evidence": self.strong_evidence,
            "weak_evidence": self.weak_evidence,
            "field_alignment": {
                "brand_match": self.field_alignment.brand_match,
                "brand_a": self.field_alignment.brand_a,
                "brand_b": self.field_alignment.brand_b,
                "spec_match": self.field_alignment.spec_match,
                "spec_a": self.field_alignment.spec_a,
                "spec_b": self.field_alignment.spec_b,
                "title_similarity": self.field_alignment.title_similarity,
                "price_band_match": self.field_alignment.price_band_match,
            },
            "missing_fields": self.missing_fields,
        }


@dataclass
class MatchCandidate:
    """A candidate match pair with scoring details."""

    tiktok_item: StandardizedItem
    shopee_item: StandardizedItem
    scoring_detail: ScoringDetail = field(default_factory=ScoringDetail)
    confidence: float = 0.0
    match_type: str = "no_match"
    status: str = "no_match"
    reasons: MatchReasons = field(default_factory=MatchReasons)
    preliminary_score: float = 0.0

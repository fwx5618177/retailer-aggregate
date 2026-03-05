"""Tests for fusion scorer."""

from sea_matching.models.match_result import StandardizedItem
from sea_matching.scoring.fusion import FusionScorer


def test_exact_match_high_confidence(dove_tiktok, dove_shopee):
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(dove_tiktok, dove_shopee)
    assert confidence > 0.80
    assert detail.brand_score >= 0.95
    assert detail.spec_score >= 0.90


def test_variant_match_moderate_confidence(dove_tiktok, dove_variant_shopee):
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(dove_tiktok, dove_variant_shopee)
    assert 0.40 < confidence < 0.90
    assert detail.brand_score >= 0.95  # Same brand
    assert detail.spec_score < 0.90  # Different spec


def test_no_match_low_confidence(dove_tiktok, nivea_shopee):
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(dove_tiktok, nivea_shopee)
    assert confidence < 0.70
    assert detail.brand_score < 0.5  # Different brand


def test_match_type_exact(dove_tiktok, dove_shopee):
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(dove_tiktok, dove_shopee)
    match_type = scorer.determine_match_type(detail, confidence)
    assert match_type == "exact_same"


def test_match_type_variant(dove_tiktok, dove_variant_shopee):
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(dove_tiktok, dove_variant_shopee)
    match_type = scorer.determine_match_type(detail, confidence)
    assert match_type in ("variant_family", "similar")


def test_missing_brand_neutral():
    item_a = StandardizedItem(
        platform="tiktok", item_id="tt_x", title="Mystery Product 500ml",
        category="personal_care", rank=1, size_value=500, size_unit="ml",
        list_price=15000, currency="THB",
    )
    item_b = StandardizedItem(
        platform="shopee", item_id="sh_x", title="Mystery Product 500ml Bottle",
        category="personal_care", rank=2, size_value=500, size_unit="ml",
        list_price=15500, currency="THB",
    )
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    confidence, detail = scorer.score(item_a, item_b)
    assert detail.brand_score == 0.0
    # Title and spec should still contribute
    assert confidence > 0.3

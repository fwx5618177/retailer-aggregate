"""End-to-end matching test with in-memory items."""

from sea_matching.filters.currency_filter import CurrencyFilter
from sea_matching.filters.spec_filter import SpecFilter
from sea_matching.models.match_result import MatchCandidate, StandardizedItem
from sea_matching.reasons.builder import ReasonsBuilder
from sea_matching.recall.combined_recall import CombinedRecall
from sea_matching.scoring.fusion import FusionScorer
from sea_matching.threshold.decision import ThresholdDecision


def _make_items():
    """Create a realistic set of items for testing."""
    tiktok_items = [
        StandardizedItem(
            platform="tiktok", item_id="tt_001",
            title="Dove Deeply Nourishing Body Wash 500ml",
            category="personal_care", rank=1, brand_std="Dove",
            size_value=500, size_unit="ml", list_price=19900, currency="THB",
        ),
        StandardizedItem(
            platform="tiktok", item_id="tt_002",
            title="Nivea Extra White Body Lotion 400ml",
            category="personal_care", rank=2, brand_std="Nivea",
            size_value=400, size_unit="ml", list_price=17900, currency="THB",
        ),
        StandardizedItem(
            platform="tiktok", item_id="tt_003",
            title="Garnier Micellar Cleansing Water 400ml",
            category="personal_care", rank=3, brand_std="Garnier",
            size_value=400, size_unit="ml", list_price=22900, currency="THB",
        ),
    ]
    shopee_items = [
        StandardizedItem(
            platform="shopee", item_id="sh_001",
            title="Dove Body Wash Deeply Nourishing 500ml Bottle",
            category="personal_care", rank=3, brand_std="Dove",
            size_value=500, size_unit="ml", list_price=19500, currency="THB",
        ),
        StandardizedItem(
            platform="shopee", item_id="sh_002",
            title="Dove Body Wash 200ml Travel Size",
            category="personal_care", rank=15, brand_std="Dove",
            size_value=200, size_unit="ml", list_price=9900, currency="THB",
        ),
        StandardizedItem(
            platform="shopee", item_id="sh_003",
            title="Nivea Extra White Lotion 400ml SPF33",
            category="personal_care", rank=5, brand_std="Nivea",
            size_value=400, size_unit="ml", list_price=17500, currency="THB",
        ),
        StandardizedItem(
            platform="shopee", item_id="sh_004",
            title="Garnier Micellar Water Pink 400ml",
            category="personal_care", rank=7, brand_std="Garnier",
            size_value=400, size_unit="ml", list_price=21900, currency="THB",
        ),
        StandardizedItem(
            platform="shopee", item_id="sh_005",
            title="Pantene Pro-V Shampoo 400ml",
            category="personal_care", rank=10, brand_std="Pantene",
            size_value=400, size_unit="ml", list_price=16900, currency="THB",
        ),
    ]
    return tiktok_items, shopee_items


def test_e2e_matching_pipeline():
    """Test the full matching pipeline with small data."""
    tiktok_items, shopee_items = _make_items()

    # Recall
    recall = CombinedRecall(
        strategies=["brand_category", "text_similarity"],
        top_k=5,
        text_config={"method": "tfidf", "min_similarity": 0.2},
    )
    recall.build_index(shopee_items)

    # Scoring
    scorer = FusionScorer(
        weights={"brand_match": 0.30, "spec_closeness": 0.25, "title_similarity": 0.30, "price_band": 0.15}
    )
    threshold = ThresholdDecision(auto_accept=0.85, needs_review=0.65)
    reasons_builder = ReasonsBuilder()
    spec_filter = SpecFilter(tolerance_pct=10)
    currency_filter = CurrencyFilter(require_same_currency=True)

    results = []
    for tt_item in tiktok_items:
        candidates_raw = recall.recall(tt_item, shopee_items)
        candidates = [
            MatchCandidate(tiktok_item=tt_item, shopee_item=sp, preliminary_score=s)
            for sp, s in candidates_raw
        ]
        candidates = spec_filter.filter(candidates)
        candidates = currency_filter.filter(candidates)

        best = None
        for c in candidates:
            conf, detail = scorer.score(c.tiktok_item, c.shopee_item)
            c.confidence = conf
            c.scoring_detail = detail
            c.match_type = scorer.determine_match_type(detail, conf)
            c.status = threshold.decide(conf, c.match_type)
            c.reasons = reasons_builder.build(c.tiktok_item, c.shopee_item, detail, conf)
            if c.status != "no_match" and (best is None or c.confidence > best.confidence):
                best = c

        if best:
            results.append(best)

    # Assertions
    assert len(results) >= 2, f"Expected at least 2 matches, got {len(results)}"

    # Dove 500ml should match well
    dove_match = next((r for r in results if r.tiktok_item.item_id == "tt_001"), None)
    assert dove_match is not None
    assert dove_match.shopee_item.item_id == "sh_001"  # Exact match, not 200ml variant
    assert dove_match.match_type == "exact_same"
    assert dove_match.confidence > 0.75

    # Nivea should match
    nivea_match = next((r for r in results if r.tiktok_item.item_id == "tt_002"), None)
    assert nivea_match is not None
    assert nivea_match.shopee_item.item_id == "sh_003"

    # All results should have reasons
    for r in results:
        assert r.reasons is not None
        assert isinstance(r.reasons.strong_evidence, list)

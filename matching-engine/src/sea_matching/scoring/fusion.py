"""Fusion scorer: combines individual scoring signals into a final confidence."""

from __future__ import annotations

from sea_matching.models.match_result import (
    MatchCandidate,
    ScoringDetail,
    StandardizedItem,
)
from sea_matching.scoring.brand_scorer import BrandScorer
from sea_matching.scoring.price_scorer import PriceScorer
from sea_matching.scoring.spec_scorer import SpecScorer
from sea_matching.scoring.title_scorer import TitleScorer


class FusionScorer:
    """Weighted fusion of individual scoring signals."""

    def __init__(self, weights: dict[str, float], title_method: str = "token_sort_ratio"):
        self.weights = weights
        self.brand_scorer = BrandScorer()
        self.spec_scorer = SpecScorer()
        self.title_scorer = TitleScorer(method=title_method)
        self.price_scorer = PriceScorer()

    def score(self, item_a: StandardizedItem, item_b: StandardizedItem) -> tuple[float, ScoringDetail]:
        """Compute weighted fusion score.

        Returns (confidence, scoring_detail).
        """
        brand = self.brand_scorer.score(item_a, item_b)
        spec = self.spec_scorer.score(item_a, item_b)
        title = self.title_scorer.score(item_a, item_b)
        price = self.price_scorer.score(item_a, item_b)

        detail = ScoringDetail(
            brand_score=brand,
            spec_score=spec,
            title_score=title,
            price_score=price,
        )

        confidence = (
            self.weights.get("brand_match", 0.3) * brand
            + self.weights.get("spec_closeness", 0.25) * spec
            + self.weights.get("title_similarity", 0.3) * title
            + self.weights.get("price_band", 0.15) * price
        )

        return confidence, detail

    def determine_match_type(self, detail: ScoringDetail, confidence: float) -> str:
        """Determine match_type based on scoring detail and confidence.

        - exact_same: brand exact + spec very close + high confidence
        - variant_family: brand exact + spec within tolerance + moderate confidence
        - similar: moderate confidence but not exact/variant
        - no_match: low confidence
        """
        brand_exact = detail.brand_score >= 0.95
        spec_exact = detail.spec_score >= 0.90
        spec_close = detail.spec_score >= 0.60

        if brand_exact and spec_exact and confidence >= 0.75:
            return "exact_same"
        elif brand_exact and spec_close and confidence >= 0.60:
            return "variant_family"
        elif confidence >= 0.50:
            return "similar"
        else:
            return "no_match"

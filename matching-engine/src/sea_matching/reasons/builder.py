"""Build structured reasons for matching decisions."""

from __future__ import annotations

from sea_matching.models.match_result import (
    FieldAlignment,
    MatchReasons,
    ScoringDetail,
    StandardizedItem,
)


class ReasonsBuilder:
    """Build structured, human-readable reasons for matching decisions."""

    def build(
        self,
        item_a: StandardizedItem,
        item_b: StandardizedItem,
        detail: ScoringDetail,
        confidence: float,
    ) -> MatchReasons:
        """Build structured reasons from scoring details."""
        strong: list[str] = []
        weak: list[str] = []
        missing: list[str] = []

        # Brand evidence
        brand_a = item_a.brand_std or item_a.brand_raw
        brand_b = item_b.brand_std or item_b.brand_raw
        if detail.brand_score >= 0.95 and brand_a:
            strong.append(f"Brand exact match: {brand_a}")
        elif detail.brand_score >= 0.7 and brand_a and brand_b:
            weak.append(f"Brand similar: '{brand_a}' vs '{brand_b}' (score={detail.brand_score:.2f})")
        elif not brand_a or not brand_b:
            missing.append("brand")

        # Spec evidence
        spec_a = f"{item_a.size_value}{item_a.size_unit}" if item_a.size_value else None
        spec_b = f"{item_b.size_value}{item_b.size_unit}" if item_b.size_value else None
        if detail.spec_score >= 0.90 and spec_a:
            strong.append(f"Spec match: {spec_a} vs {spec_b}")
        elif detail.spec_score >= 0.60 and spec_a and spec_b:
            weak.append(f"Spec close: {spec_a} vs {spec_b} (score={detail.spec_score:.2f})")
        elif not spec_a or not spec_b:
            missing.append("size_value/size_unit")

        # Title evidence
        if detail.title_score >= 0.80:
            strong.append(f"Title high similarity: {detail.title_score:.2f}")
        elif detail.title_score >= 0.50:
            weak.append(f"Title moderate similarity: {detail.title_score:.2f}")

        # Price evidence
        if detail.price_score >= 0.80:
            weak.append(f"Price band aligned (score={detail.price_score:.2f})")
        elif item_a.list_price is None or item_b.list_price is None:
            missing.append("list_price")

        alignment = FieldAlignment(
            brand_match=detail.brand_score >= 0.95,
            brand_a=brand_a,
            brand_b=brand_b,
            spec_match=detail.spec_score >= 0.90,
            spec_a=spec_a,
            spec_b=spec_b,
            title_similarity=round(detail.title_score, 3),
            price_band_match=detail.price_score >= 0.70,
        )

        return MatchReasons(
            strong_evidence=strong,
            weak_evidence=weak,
            field_alignment=alignment,
            missing_fields=missing,
        )

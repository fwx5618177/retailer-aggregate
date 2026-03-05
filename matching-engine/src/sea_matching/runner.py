"""Main matching engine runner / orchestrator."""

from __future__ import annotations

import logging
import time
import uuid

import duckdb

from sea_matching.filters.currency_filter import CurrencyFilter
from sea_matching.filters.spec_filter import SpecFilter
from sea_matching.models.match_result import MatchCandidate, StandardizedItem
from sea_matching.output.manifest_writer import ManifestWriter
from sea_matching.output.match_writer import MatchWriter
from sea_matching.output.report_generator import ReportGenerator
from sea_matching.override.override_merger import OverrideMerger
from sea_matching.reasons.builder import ReasonsBuilder
from sea_matching.recall.combined_recall import CombinedRecall
from sea_matching.scoring.fusion import FusionScorer
from sea_matching.threshold.decision import ThresholdDecision

logger = logging.getLogger(__name__)


class MatchingRunner:
    """Main orchestrator for the matching pipeline."""

    def __init__(self, config: dict):
        self.config = config
        self.run_id = str(uuid.uuid4())[:8]
        self.batch_id = f"match-{self.run_id}"

    def run(self, event_date: str | None = None) -> dict:
        """Run the full matching pipeline.

        1. Load standardized items from source
        2. For each TikTok item, recall candidates from Shopee items
        3. Filter candidates
        4. Score candidates
        5. Apply thresholds
        6. Build reasons
        7. Merge overrides
        8. Write output
        9. Generate report
        10. Write manifest

        Returns manifest dict.
        """
        start_time = time.time()
        logger.info("Starting matching run %s", self.run_id)

        # 1. Load data
        tiktok_items, shopee_items = self._load_items(event_date)
        logger.info("Loaded %d TikTok items and %d Shopee items", len(tiktok_items), len(shopee_items))

        if not tiktok_items or not shopee_items:
            logger.warning("No items to match")
            return {"run_id": self.run_id, "status": "empty"}

        # 2. Initialize components
        recall_cfg = self.config.get("recall", {})
        recall = CombinedRecall(
            strategies=recall_cfg.get("strategies", ["brand_category", "text_similarity"]),
            top_k=recall_cfg.get("top_k", 20),
            text_config=recall_cfg.get("text_similarity", {}),
            opensearch_config=recall_cfg.get("opensearch", {}),
            vector_config=recall_cfg.get("vector", {}),
        )
        recall.build_index(shopee_items)

        filter_cfg = self.config.get("filters", {})
        spec_filter = SpecFilter(tolerance_pct=filter_cfg.get("spec_tolerance_pct", 10))
        currency_filter = CurrencyFilter(require_same_currency=filter_cfg.get("require_same_currency", True))

        scoring_cfg = self.config.get("scoring", {})
        scorer = FusionScorer(
            weights=scoring_cfg.get("weights", {}),
            title_method=scoring_cfg.get("title_similarity_method", "token_sort_ratio"),
        )

        threshold_cfg = self.config.get("thresholds", {})
        threshold = ThresholdDecision(
            auto_accept=threshold_cfg.get("auto_accept", 0.85),
            needs_review=threshold_cfg.get("needs_review", 0.65),
        )

        reasons_builder = ReasonsBuilder()

        override_cfg = self.config.get("override", {})
        override_merger = OverrideMerger(
            overrides_path=override_cfg.get("overrides_path") if override_cfg.get("merge_overrides") else None
        )

        rule_version = self.config.get("matching", {}).get("rule_version", "1.0.0")

        # 3. Match each TikTok item against Shopee candidates
        all_candidates: list[MatchCandidate] = []
        best_matches: dict[str, MatchCandidate] = {}  # Track best match per TikTok item

        for i, tt_item in enumerate(tiktok_items):
            if (i + 1) % 50 == 0:
                logger.info("Processing TikTok item %d/%d", i + 1, len(tiktok_items))

            # Recall
            recalled = recall.recall(tt_item, shopee_items)
            if not recalled:
                continue

            # Build candidates
            candidates = [
                MatchCandidate(tiktok_item=tt_item, shopee_item=sp_item, preliminary_score=score)
                for sp_item, score in recalled
            ]

            # Filter
            candidates = spec_filter.filter(candidates)
            candidates = currency_filter.filter(candidates)

            # Score, classify, build reasons
            for candidate in candidates:
                confidence, detail = scorer.score(candidate.tiktok_item, candidate.shopee_item)
                candidate.confidence = confidence
                candidate.scoring_detail = detail
                candidate.match_type = scorer.determine_match_type(detail, confidence)
                candidate.status = threshold.decide(confidence, candidate.match_type)
                candidate.reasons = reasons_builder.build(
                    candidate.tiktok_item, candidate.shopee_item, detail, confidence
                )

            # Keep the best match per TikTok item
            for candidate in candidates:
                if candidate.status != "no_match":
                    key = candidate.tiktok_item.item_id
                    if key not in best_matches or candidate.confidence > best_matches[key].confidence:
                        best_matches[key] = candidate

            all_candidates.extend(candidates)

        # Collect results: best matches + any no_match items
        results = list(best_matches.values())
        logger.info("Found %d matched pairs out of %d TikTok items", len(results), len(tiktok_items))

        # 4. Merge overrides
        results = override_merger.merge(results)

        # 5. Write output
        output_cfg = self.config.get("output", {})
        writer = MatchWriter()

        if output_cfg.get("format") == "parquet":
            writer.write_parquet(
                results,
                output_dir=output_cfg.get("output_dir", "data/matching_output"),
                event_date=event_date or "latest",
                run_id=self.run_id,
                rule_version=rule_version,
                batch_id=self.batch_id,
            )

        if output_cfg.get("duckdb_path"):
            writer.write_duckdb(
                results,
                db_path=output_cfg["duckdb_path"],
                rule_version=rule_version,
                batch_id=self.batch_id,
                run_id=self.run_id,
            )

        # 6. Generate report
        if output_cfg.get("generate_report"):
            report_gen = ReportGenerator(
                sample_size=output_cfg.get("report_sample_size", 50)
            )
            report_gen.generate(
                results,
                report_dir=output_cfg.get("report_dir", "reports"),
                run_id=self.run_id,
            )

        # 7. Write manifest
        duration = time.time() - start_time
        result_counts = {
            "total_tiktok": len(tiktok_items),
            "total_shopee": len(shopee_items),
            "total_candidates": len(all_candidates),
            "matched_pairs": len(results),
            "auto_accepted": sum(1 for r in results if r.status == "auto_accepted"),
            "needs_review": sum(1 for r in results if r.status == "needs_review"),
            "overridden": sum(1 for r in results if r.status == "overridden"),
        }

        manifest_writer = ManifestWriter()
        manifest_path = manifest_writer.write(
            output_dir=output_cfg.get("output_dir", "data/matching_output"),
            event_date=event_date or "latest",
            run_id=self.run_id,
            batch_id=self.batch_id,
            rule_version=rule_version,
            parameters={
                "recall_strategies": recall_cfg.get("strategies", []),
                "top_k": recall_cfg.get("top_k", 20),
                "scoring_weights": scoring_cfg.get("weights", {}),
                "thresholds": threshold_cfg,
            },
            result_counts=result_counts,
            duration_seconds=duration,
        )

        logger.info(
            "Matching complete: %d pairs in %.1fs (auto=%d, review=%d)",
            len(results), duration,
            result_counts["auto_accepted"],
            result_counts["needs_review"],
        )

        return {
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "manifest_path": manifest_path,
            "result_counts": result_counts,
            "duration_seconds": round(duration, 2),
        }

    def _load_items(self, event_date: str | None) -> tuple[list[StandardizedItem], list[StandardizedItem]]:
        """Load standardized items from DuckDB or Parquet."""
        input_cfg = self.config.get("input", {})
        source = input_cfg.get("source", "duckdb")

        if source == "duckdb":
            return self._load_from_duckdb(input_cfg, event_date)
        else:
            return self._load_from_parquet(input_cfg, event_date)

    def _load_from_duckdb(
        self, input_cfg: dict, event_date: str | None
    ) -> tuple[list[StandardizedItem], list[StandardizedItem]]:
        """Load items from DuckDB."""
        db_path = input_cfg.get("duckdb_path", "../data-pipeline/data/pipeline.duckdb")
        category = input_cfg.get("category", "personal_care")

        conn = duckdb.connect(db_path, read_only=True)

        # Get the latest event_date if not specified
        if not event_date:
            result = conn.execute("SELECT MAX(event_date) FROM top_items").fetchone()
            event_date = str(result[0]) if result and result[0] else None
            if not event_date:
                conn.close()
                return [], []

        query = """
            SELECT t.*, p.price AS list_price, p.promo_price, p.currency
            FROM top_items t
            LEFT JOIN price_snapshots p
                ON t.platform = p.platform
                AND t.item_id = p.item_id
                AND t.event_date = p.event_date
            WHERE t.event_date = ?
              AND t.category = ?
        """
        rows = conn.execute(query, [event_date, category]).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()

        tiktok_items = []
        shopee_items = []

        for row in rows:
            data = dict(zip(columns, row))
            item = StandardizedItem(
                platform=data.get("platform", ""),
                item_id=data.get("item_id", ""),
                title=data.get("title", ""),
                category=data.get("category", ""),
                rank=data.get("rank", 0),
                brand_raw=data.get("brand_raw"),
                brand_std=data.get("brand_std"),
                size_value=data.get("size_value"),
                size_unit=data.get("size_unit"),
                pack_count=data.get("pack_count"),
                list_price=data.get("list_price"),
                promo_price=data.get("promo_price"),
                currency=data.get("currency"),
                url=data.get("url"),
                event_date=str(data.get("event_date", "")),
            )
            if item.platform == "tiktok":
                tiktok_items.append(item)
            elif item.platform == "shopee":
                shopee_items.append(item)

        return tiktok_items, shopee_items

    def _load_from_parquet(
        self, input_cfg: dict, event_date: str | None
    ) -> tuple[list[StandardizedItem], list[StandardizedItem]]:
        """Load items from Parquet files."""
        import pyarrow.parquet as pq
        from pathlib import Path

        parquet_dir = Path(input_cfg.get("parquet_dir", "../data-pipeline/data/serving"))

        # Find latest event_date directory if not specified
        if not event_date:
            date_dirs = sorted([d.name for d in parquet_dir.iterdir() if d.is_dir()], reverse=True)
            if not date_dirs:
                return [], []
            event_date = date_dirs[0]

        # Find latest run_id
        date_path = parquet_dir / event_date
        if not date_path.exists():
            return [], []
        run_dirs = sorted([d.name for d in date_path.iterdir() if d.is_dir()], reverse=True)
        if not run_dirs:
            return [], []

        data_path = date_path / run_dirs[0]
        top_items_file = data_path / "top_items.parquet"
        prices_file = data_path / "price_snapshots.parquet"

        if not top_items_file.exists():
            return [], []

        # Read top_items
        table = pq.read_table(top_items_file)
        items_df = table.to_pydict()

        # Read prices if available
        prices: dict[str, dict] = {}
        if prices_file.exists():
            price_table = pq.read_table(prices_file)
            price_df = price_table.to_pydict()
            for i in range(len(price_df.get("item_id", []))):
                key = f"{price_df['platform'][i]}:{price_df['item_id'][i]}"
                prices[key] = {
                    "list_price": price_df.get("price", price_df.get("list_price", [None]))[i],
                    "promo_price": price_df.get("promo_price", [None])[i],
                    "currency": price_df.get("currency", [None])[i],
                }

        tiktok_items = []
        shopee_items = []

        num_items = len(items_df.get("item_id", []))
        for i in range(num_items):
            platform = items_df["platform"][i]
            item_id = items_df["item_id"][i]
            price_key = f"{platform}:{item_id}"
            price_data = prices.get(price_key, {})

            item = StandardizedItem(
                platform=platform,
                item_id=item_id,
                title=items_df.get("title", [""])[i] or "",
                category=items_df.get("category", [""])[i] or "",
                rank=items_df.get("rank", [0])[i] or 0,
                brand_raw=items_df.get("brand_raw", [None])[i],
                brand_std=items_df.get("brand_std", [None])[i],
                size_value=items_df.get("size_value", [None])[i],
                size_unit=items_df.get("size_unit", [None])[i],
                pack_count=items_df.get("pack_count", [None])[i],
                list_price=price_data.get("list_price"),
                promo_price=price_data.get("promo_price"),
                currency=price_data.get("currency"),
                event_date=str(items_df.get("event_date", [""])[i] or ""),
            )
            if platform == "tiktok":
                tiktok_items.append(item)
            elif platform == "shopee":
                shopee_items.append(item)

        return tiktok_items, shopee_items

"""PipelineRunner -- main orchestrator for the SEA data pipeline."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sea_pipeline.config import PipelineConfig
from sea_pipeline.dq.checks import DQChecker, DQResult
from sea_pipeline.dq.gates import DQGate, DQStatus
from sea_pipeline.export.duckdb_writer import DuckDBWriter
from sea_pipeline.export.manifest_writer import ManifestWriter
from sea_pipeline.export.parquet_exporter import ParquetExporter
from sea_pipeline.ingestion.shopee_adapter import ShopeeAdapter
from sea_pipeline.ingestion.tiktok_adapter import TiktokAdapter
from sea_pipeline.logging_config import setup_logging
from sea_pipeline.standardisation.brand_normalizer import BrandNormalizer
from sea_pipeline.standardisation.currency_handler import CurrencyHandler
from sea_pipeline.standardisation.spec_parser import SpecParser
from sea_pipeline.standardisation.std_cache import StandardisationCache
from sea_pipeline.storage.raw_cache import RawCache

logger = logging.getLogger("sea_pipeline")


@dataclass
class RunManifest:
    """Summary of a pipeline run returned by ``PipelineRunner.run``."""

    run_id: str
    batch_id: str
    event_date: str
    dq_status: str
    dq_results: list[DQResult] = field(default_factory=list)
    row_counts: dict[str, int] = field(default_factory=dict)
    alerts_count: int = 0
    duration_seconds: float = 0.0
    manifest_path: str = ""


class PipelineRunner:
    """Orchestrates a complete data-pipeline run.

    Steps
    -----
    1. Generate ``run_id`` and ``batch_id``.
    2. For each (platform, category, site):
       a. Ingest via adapter (or stub).
       b. Cache raw response.
       c. Standardise (brand, spec, currency).
       d. Write to DuckDB (top_items, price_snapshots, sales_proxy).
    3. Generate alerts (rank-jump detection).
    4. Run DQ checks.
    5. Apply DQ gate.
    6. Export to Parquet.
    7. Write manifest.
    8. Return manifest.
    """

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.brand_normalizer = BrandNormalizer(config.standardisation.brand_dictionary_path)
        self.spec_parser = SpecParser()
        self.currency_handler = CurrencyHandler()
        self.dq_checker = DQChecker()
        self.dq_gate = DQGate()
        self.db_writer = DuckDBWriter(config.storage.duckdb_path)
        self.parquet_exporter = ParquetExporter()
        self.manifest_writer = ManifestWriter()
        self.raw_cache = RawCache()
        self.std_cache = StandardisationCache(
            cache_path=Path(config.storage.duckdb_path).parent / "std_cache.json",
        )

    def _get_adapter(self, platform: str, event_date: date):
        """Return the appropriate adapter for *platform*."""
        ing = self.config.ingestion
        if platform == "shopee":
            return ShopeeAdapter(
                endpoint_config=ing.shopee,
                rate_limit_config=ing.rate_limit,
                use_stub=ing.use_stub,
                stub_fallback=ing.stub_fallback,
                event_date=event_date,
            )
        elif platform == "tiktok":
            return TiktokAdapter(
                endpoint_config=ing.tiktok,
                rate_limit_config=ing.rate_limit,
                use_stub=ing.use_stub,
                stub_fallback=ing.stub_fallback,
                event_date=event_date,
            )
        else:
            raise ValueError(f"Unknown platform: {platform}")

    def _standardise_item(
        self,
        item: dict,
        platform: str,
        site: str,
        event_date_str: str,
        run_id: str,
        batch_id: str,
    ) -> dict:
        """Enrich an item dict with standardised fields."""
        title = item.get("title", "")

        # Check standardisation cache first
        cached = self.std_cache.get(title) if title else None
        if cached is not None:
            brand_std, spec = cached
        else:
            # Brand
            brand_std = self.brand_normalizer.normalize(item.get("brand_raw", ""))
            if brand_std is None:
                # Try extracting brand from title
                brand_std = self.brand_normalizer.normalize(title)

            # Spec
            spec = self.spec_parser.parse(title)

            # Store in cache
            if title:
                self.std_cache.put(title, brand_std, spec)

        # Currency
        currency = item.get("currency", self.currency_handler.currency_for_site(site))

        # Compute price-per-unit
        price = item.get("price", 0) or 0
        price_per_ml = None
        price_per_g = None

        if spec.normalized_value and spec.normalized_value > 0:
            if spec.normalized_unit == "ml":
                price_per_ml = price / spec.normalized_value
            elif spec.normalized_unit == "g":
                price_per_g = price / spec.normalized_value

        return {
            **item,
            "platform": platform,
            "site": site,
            "event_date": event_date_str,
            "brand_std": brand_std,
            "size_value": spec.size_value,
            "size_unit": spec.size_unit,
            "pack_count": spec.pack_count,
            "normalized_ml": spec.normalized_value if spec.normalized_unit == "ml" else None,
            "normalized_g": spec.normalized_value if spec.normalized_unit == "g" else None,
            "currency": currency,
            "price_per_ml": price_per_ml,
            "price_per_g": price_per_g,
            "run_id": run_id,
            "batch_id": batch_id,
        }

    @staticmethod
    def _expand_sales_proxies(
        items: list[dict],
        event_date_str: str,
        platform: str,
        run_id: str,
        batch_id: str,
    ) -> list[dict]:
        """Expand flat proxy fields into normalised rows for ``sales_proxy``.

        The ``sales_proxy`` table stores one row per (item, proxy_type).
        Raw item dicts carry ``review_count``, ``rating``, ``sold_range``,
        ``likes`` as separate keys.  This method unpivots them.
        """
        _PROXY_FIELDS: list[tuple[str, str]] = [
            ("review_count", "review_count"),
            ("rating", "rating"),
            ("sold_range", "sold_range"),
            ("likes", "likes"),
        ]

        rows: list[dict] = []
        for item in items:
            for field_key, proxy_type in _PROXY_FIELDS:
                raw = item.get(field_key)
                if raw is None:
                    continue
                # proxy_numeric: attempt float conversion; proxy_value: string
                try:
                    numeric = float(raw)
                except (TypeError, ValueError):
                    numeric = None
                rows.append({
                    "event_date": event_date_str,
                    "platform": platform,
                    "item_id": item["item_id"],
                    "proxy_type": proxy_type,
                    "proxy_value": str(raw),
                    "proxy_numeric": numeric,
                    "run_id": run_id,
                    "batch_id": batch_id,
                })
        return rows

    def _detect_alerts(
        self,
        items: list[dict],
        platform: str,
        event_date_str: str,
        run_id: str,
    ) -> list[dict]:
        """Detect alerts across four categories: rank_jump, proxy_spike,
        platform_gap, and price_anomaly."""
        alerts: list[dict] = []

        # Load previous data for rank-jump and proxy-spike detection
        prev_rank_map: dict[str, int] = {}
        prev_proxy_map: dict[str, dict[str, float]] = {}
        try:
            from sea_pipeline.storage.local_store import LocalStore

            store = LocalStore(self.config.storage.duckdb_path)
            prev_rows = store.query(
                "SELECT item_id, rank FROM top_items "
                "WHERE platform = ? AND event_date < ? "
                "ORDER BY event_date DESC LIMIT 200",
                [platform, event_date_str],
            )
            prev_rank_map = {r["item_id"]: r["rank"] for r in prev_rows}

            # Previous proxy values for spike detection
            proxy_rows = store.query(
                "SELECT item_id, proxy_type, proxy_numeric FROM sales_proxy "
                "WHERE platform = ? AND event_date < ? AND proxy_numeric IS NOT NULL "
                "ORDER BY event_date DESC",
                [platform, event_date_str],
            )
            for r in proxy_rows:
                prev_proxy_map.setdefault(r["item_id"], {})[r["proxy_type"]] = r["proxy_numeric"]
        except Exception:
            pass

        # Compute category median price for anomaly detection
        prices = [
            item.get("price", 0)
            for item in items
            if item.get("price") and item["price"] > 0
        ]
        median_price = sorted(prices)[len(prices) // 2] if prices else 0

        for item in items:
            item_id = item.get("item_id", "")
            rank = item.get("rank", 0)

            # 1. Rank-jump detection (>=50 positions change)
            if item_id in prev_rank_map:
                prev_rank = prev_rank_map[item_id]
                jump = abs(rank - prev_rank)
                if jump >= 50:
                    direction = "up" if rank < prev_rank else "down"
                    severity = "high" if jump >= 100 else "medium"
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "event_date": event_date_str,
                        "platform": platform,
                        "item_id": item_id,
                        "alert_type": "rank_jump",
                        "severity": severity,
                        "status": "open",
                        "message": f"Rank jumped {jump} positions {direction} ({prev_rank} -> {rank})",
                        "details": f'{{"prev_rank":{prev_rank},"new_rank":{rank},"jump":{jump},"direction":"{direction}"}}',
                        "suggested_action": f"Investigate why {item.get('title', item_id)} moved {direction} by {jump} ranks",
                        "run_id": run_id,
                    })

            # 2. Proxy-spike detection (review_count or sold_range growth >50%)
            if item_id in prev_proxy_map:
                for proxy_type in ("review_count", "likes", "sold"):
                    cur_val = item.get(f"proxy_{proxy_type}") or item.get(proxy_type)
                    if cur_val is None:
                        continue
                    try:
                        cur_num = float(cur_val)
                    except (TypeError, ValueError):
                        continue
                    prev_num = prev_proxy_map[item_id].get(proxy_type)
                    if prev_num and prev_num > 0:
                        growth = (cur_num - prev_num) / prev_num
                        if growth >= 0.5:
                            severity = "high" if growth >= 1.0 else "medium"
                            alerts.append({
                                "alert_id": str(uuid.uuid4()),
                                "event_date": event_date_str,
                                "platform": platform,
                                "item_id": item_id,
                                "alert_type": "proxy_spike",
                                "severity": severity,
                                "status": "open",
                                "message": f"{proxy_type} grew {growth:.0%} ({prev_num:.0f} -> {cur_num:.0f})",
                                "details": f'{{"proxy_type":"{proxy_type}","prev":{prev_num:.0f},"current":{cur_num:.0f},"growth":{growth:.2f}}}',
                                "suggested_action": f"Review demand surge for {item.get('title', item_id)}",
                                "run_id": run_id,
                            })

            # 3. Price anomaly: zero/negative OR >3x or <0.2x category median
            price = item.get("price", 0)
            if price is not None and price <= 0:
                alerts.append({
                    "alert_id": str(uuid.uuid4()),
                    "event_date": event_date_str,
                    "platform": platform,
                    "item_id": item_id,
                    "alert_type": "price_anomaly",
                    "severity": "high",
                    "status": "open",
                    "message": f"Price is {price} (zero or negative)",
                    "details": f'{{"price":{price},"median":{median_price}}}',
                    "suggested_action": "Verify listing price — possible data quality issue",
                    "run_id": run_id,
                })
            elif median_price > 0 and price:
                ratio = price / median_price
                if ratio > 3.0 or ratio < 0.2:
                    label = "above" if ratio > 3.0 else "below"
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "event_date": event_date_str,
                        "platform": platform,
                        "item_id": item_id,
                        "alert_type": "price_anomaly",
                        "severity": "medium",
                        "status": "open",
                        "message": f"Price {ratio:.1f}x category median ({price/100:.0f} vs {median_price/100:.0f} THB)",
                        "details": f'{{"price":{price},"median":{median_price},"ratio":{ratio:.2f}}}',
                        "suggested_action": f"Check if price is correct — significantly {label} category average",
                        "run_id": run_id,
                    })

        return alerts

    def _detect_platform_gap_alerts(
        self,
        all_items: list[dict],
        event_date_str: str,
        run_id: str,
    ) -> list[dict]:
        """Detect items that are top-ranked on one platform but absent or
        low-ranked on the other (platform_gap alert)."""
        alerts: list[dict] = []

        # Build {brand_std -> {platform -> best_rank}} index
        tt_items = {i["item_id"]: i for i in all_items if i.get("platform") == "tiktok"}
        sh_items = {i["item_id"]: i for i in all_items if i.get("platform") == "shopee"}

        tt_brands: dict[str, dict] = {}
        for item in tt_items.values():
            brand = item.get("brand_std")
            if brand and (brand not in tt_brands or item.get("rank", 999) < tt_brands[brand].get("rank", 999)):
                tt_brands[brand] = item

        sh_brands: dict[str, dict] = {}
        for item in sh_items.values():
            brand = item.get("brand_std")
            if brand and (brand not in sh_brands or item.get("rank", 999) < sh_brands[brand].get("rank", 999)):
                sh_brands[brand] = item

        # Find brands in top-50 on one platform but absent or rank>150 on the other
        rank_threshold_top = 50
        rank_threshold_low = 150

        for brand, tt_item in tt_brands.items():
            if tt_item.get("rank", 999) <= rank_threshold_top:
                sh_item = sh_brands.get(brand)
                if sh_item is None or sh_item.get("rank", 999) > rank_threshold_low:
                    sh_rank = sh_item.get("rank", "absent") if sh_item else "absent"
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "event_date": event_date_str,
                        "platform": "tiktok",
                        "item_id": tt_item["item_id"],
                        "alert_type": "platform_gap",
                        "severity": "medium",
                        "status": "open",
                        "message": f"{brand} is rank {tt_item['rank']} on TikTok but {sh_rank} on Shopee",
                        "details": f'{{"brand":"{brand}","tiktok_rank":{tt_item["rank"]},"shopee_rank":"{sh_rank}"}}',
                        "suggested_action": f"Opportunity: {brand} is popular on TikTok but underperforming on Shopee",
                        "run_id": run_id,
                    })

        for brand, sh_item in sh_brands.items():
            if sh_item.get("rank", 999) <= rank_threshold_top:
                tt_item = tt_brands.get(brand)
                if tt_item is None or tt_item.get("rank", 999) > rank_threshold_low:
                    tt_rank = tt_item.get("rank", "absent") if tt_item else "absent"
                    alerts.append({
                        "alert_id": str(uuid.uuid4()),
                        "event_date": event_date_str,
                        "platform": "shopee",
                        "item_id": sh_item["item_id"],
                        "alert_type": "platform_gap",
                        "severity": "medium",
                        "status": "open",
                        "message": f"{brand} is rank {sh_item['rank']} on Shopee but {tt_rank} on TikTok",
                        "details": f'{{"brand":"{brand}","shopee_rank":{sh_item["rank"]},"tiktok_rank":"{tt_rank}"}}',
                        "suggested_action": f"Opportunity: {brand} is popular on Shopee but underperforming on TikTok",
                        "run_id": run_id,
                    })

        return alerts

    def run(
        self,
        event_date: date | str | None = None,
        run_id: str | None = None,
    ) -> RunManifest:
        """Execute the full pipeline and return the manifest.

        Parameters
        ----------
        event_date:
            Override event date (default: today).
        run_id:
            Override run ID (default: new UUID).
        """
        start = time.monotonic()

        # 1. Generate identifiers
        if run_id is None:
            run_id = str(uuid.uuid4())
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

        if event_date is None:
            event_date = date.today()
        if isinstance(event_date, str):
            event_date = date.fromisoformat(event_date)
        event_date_str = event_date.isoformat()

        # Set up logging with context
        setup_logging(
            run_id=run_id,
            batch_id=batch_id,
            event_date=event_date_str,
        )
        logger.info("Pipeline run started: run_id=%s, event_date=%s", run_id, event_date_str)

        # 2. Initialise DuckDB
        self.db_writer.init_tables()

        scope = self.config.scope
        all_items: list[dict] = []
        all_alerts: list[dict] = []
        all_dq_results: list[DQResult] = []

        # 3. Process each platform x category x site
        for platform in scope.platforms:
            for category in scope.categories:
                for site in scope.sites:
                    logger.info(
                        "Processing %s / %s / %s",
                        platform,
                        category,
                        site,
                    )

                    # a. Ingest
                    adapter = self._get_adapter(platform, event_date)
                    raw_items = asyncio.run(
                        adapter.fetch_top_items(category, site, scope.top_n)
                    )
                    parsed_items = adapter.parse_response(raw_items)
                    logger.info(
                        "Ingested %d items from %s/%s/%s",
                        len(parsed_items),
                        platform,
                        category,
                        site,
                    )

                    # b. Cache raw response
                    self.raw_cache.save(platform, category, event_date_str, raw_items)

                    # c. Standardise
                    enriched = [
                        self._standardise_item(
                            item, platform, site, event_date_str, run_id, batch_id,
                        )
                        for item in parsed_items
                    ]

                    # d. Write to DuckDB
                    self.db_writer.write_top_items(enriched)

                    price_snapshots = [
                        {
                            "event_date": event_date_str,
                            "platform": platform,
                            "item_id": item["item_id"],
                            "price": item.get("price", 0),
                            "promo_price": item.get("promo_price"),
                            "currency": item.get("currency", "THB"),
                            "price_per_ml": item.get("price_per_ml"),
                            "price_per_g": item.get("price_per_g"),
                            "run_id": run_id,
                            "batch_id": batch_id,
                        }
                        for item in enriched
                    ]
                    self.db_writer.write_price_snapshots(price_snapshots)

                    sales_proxies = self._expand_sales_proxies(
                        enriched, event_date_str, platform, run_id, batch_id,
                    )
                    self.db_writer.write_sales_proxy(sales_proxies)

                    all_items.extend(enriched)

                    # 3. Generate alerts
                    alerts = self._detect_alerts(
                        enriched, platform, event_date_str, run_id,
                    )
                    all_alerts.extend(alerts)

                    # 4. Run DQ checks per platform/category
                    currency = self.currency_handler.currency_for_site(site)
                    dq_data = {
                        "items": enriched,
                        "platform": platform,
                        "expected_n": scope.top_n,
                        "currency": currency,
                    }
                    dq_config = self.config.dq.model_dump()
                    dq_results = self.dq_checker.run_all(dq_data, dq_config)
                    all_dq_results.extend(dq_results)

        # Cross-platform gap alerts (needs all items from both platforms)
        gap_alerts = self._detect_platform_gap_alerts(all_items, event_date_str, run_id)
        all_alerts.extend(gap_alerts)

        # Write all alerts
        self.db_writer.write_alerts(all_alerts)

        # 5. Apply DQ gate
        dq_status, _ = self.dq_gate.evaluate(all_dq_results, self.config.dq.mode)

        # 6. Export to Parquet (skip if FAILED in block mode)
        row_counts: dict[str, int] = {}
        if dq_status != DQStatus.FAILED:
            row_counts = self.parquet_exporter.export_to_parquet(
                self.config.storage.duckdb_path,
                self.config.export.serving_dir,
                event_date_str,
                run_id,
            )
        else:
            logger.error("DQ gate FAILED -- skipping Parquet export.")

        duration = time.monotonic() - start

        # 7. Write manifest
        parameters = {
            "platforms": scope.platforms,
            "categories": scope.categories,
            "sites": scope.sites,
            "top_n": scope.top_n,
            "use_stub": self.config.ingestion.use_stub,
        }
        manifest_path = self.manifest_writer.write(
            output_dir=self.config.export.serving_dir,
            event_date=event_date_str,
            run_id=run_id,
            batch_id=batch_id,
            parameters=parameters,
            row_counts=row_counts,
            dq_results=all_dq_results,
            dq_status=dq_status.value,
            duration_seconds=duration,
        )

        logger.info(
            "Pipeline run completed: run_id=%s, status=%s, duration=%.2fs",
            run_id,
            dq_status.value,
            duration,
        )

        # Persist standardisation cache for next incremental run
        self.std_cache.save()
        logger.info("Standardisation cache stats: %s", self.std_cache.stats)

        return RunManifest(
            run_id=run_id,
            batch_id=batch_id,
            event_date=event_date_str,
            dq_status=dq_status.value,
            dq_results=all_dq_results,
            row_counts=row_counts,
            alerts_count=len(all_alerts),
            duration_seconds=round(duration, 2),
            manifest_path=str(manifest_path),
        )

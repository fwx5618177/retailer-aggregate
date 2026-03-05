"""TikTok Shop platform adapter -- fetches top items or uses stub data."""

from __future__ import annotations

import logging
from datetime import date

import httpx

from sea_pipeline.config import PlatformEndpointConfig, RateLimitConfig
from sea_pipeline.ingestion.base import BasePlatformAdapter
from sea_pipeline.ingestion.rate_limiter import RateLimiter
from sea_pipeline.ingestion.stub_loader import StubLoader

logger = logging.getLogger("sea_pipeline")

SITE_DOMAIN = {
    "th": "www.tiktok.com",
    "sg": "www.tiktok.com",
    "my": "www.tiktok.com",
    "id": "www.tiktok.com",
    "ph": "www.tiktok.com",
    "vn": "www.tiktok.com",
}

CATEGORY_KEYWORD = {
    "personal_care": "personal care",
}


class TiktokAdapter(BasePlatformAdapter):
    """Adapter for fetching top items from TikTok Shop."""

    def __init__(
        self,
        endpoint_config: PlatformEndpointConfig | None = None,
        rate_limit_config: RateLimitConfig | None = None,
        use_stub: bool = False,
        stub_fallback: bool = True,
        stub_root: str = "data/raw_stub",
        event_date: date | None = None,
    ) -> None:
        self.endpoint = endpoint_config or PlatformEndpointConfig()
        rl = rate_limit_config or RateLimitConfig()
        self.rate_limiter = RateLimiter(
            requests_per_second=rl.requests_per_second,
            max_concurrent=rl.max_concurrent,
        )
        self.backoff_factor = rl.backoff_factor
        self.max_retries = rl.max_retries
        self.use_stub = use_stub
        self.stub_fallback = stub_fallback
        self.stub_loader = StubLoader(stub_root)
        self.event_date = event_date or date.today()

    async def fetch_top_items(
        self,
        category: str,
        site: str,
        top_n: int,
    ) -> list[dict]:
        """Fetch top-N items from TikTok Shop for *category* / *site*."""

        if self.use_stub:
            logger.info("Using stub data for tiktok/%s", category)
            return self.stub_loader.load("tiktok", category, self.event_date)

        try:
            return await self._fetch_live(category, site, top_n)
        except Exception as exc:
            logger.error("TikTok live fetch failed: %s", exc)
            if self.stub_fallback:
                logger.info("Falling back to stub data for tiktok/%s", category)
                return self.stub_loader.load("tiktok", category, self.event_date)
            raise

    async def _fetch_live(
        self,
        category: str,
        site: str,
        top_n: int,
    ) -> list[dict]:
        """Paginated fetch from TikTok Shop API."""
        base_url = self.endpoint.base_url or "https://www.tiktok.com/api/v1/shop"
        search_url = (
            f"{base_url}{self.endpoint.search_endpoint or '/products/search'}"
        )
        keyword = CATEGORY_KEYWORD.get(category, category)
        items: list[dict] = []
        page_size = 50
        page = 1

        async with httpx.AsyncClient(timeout=self.endpoint.timeout) as client:
            while len(items) < top_n:
                params = {
                    "keyword": keyword,
                    "page": page,
                    "page_size": min(page_size, top_n - len(items)),
                    "region": site,
                    "sort_by": "relevance",
                }
                attempt = 0
                response = None
                while attempt <= self.max_retries:
                    try:
                        async with self.rate_limiter.acquire():
                            response = await client.get(search_url, params=params)
                        response.raise_for_status()
                        break
                    except (httpx.HTTPStatusError, httpx.RequestError) as err:
                        attempt += 1
                        if attempt > self.max_retries:
                            raise
                        wait = self.backoff_factor ** attempt
                        logger.warning(
                            "TikTok request failed (attempt %d/%d), retrying in %.1fs: %s",
                            attempt,
                            self.max_retries,
                            wait,
                            err,
                        )
                        import asyncio
                        await asyncio.sleep(wait)

                if response is None:
                    break

                data = response.json()
                page_items = data.get("products", data.get("items", []))
                if not page_items:
                    break

                for raw_item in page_items:
                    items.append({
                        "item_id": f"tt_{raw_item.get('product_id', raw_item.get('item_id', ''))}",
                        "title": raw_item.get("title", raw_item.get("name", "")),
                        "category": category,
                        "rank": len(items) + 1,
                        "url": f"https://www.tiktok.com/shop/product/{raw_item.get('product_id', '')}",
                        "image_url": raw_item.get("cover", raw_item.get("image_url", "")),
                        "price": raw_item.get("price", 0),
                        "promo_price": raw_item.get("promo_price"),
                        "currency": "THB" if site == "th" else site.upper(),
                        "brand_raw": raw_item.get("brand", raw_item.get("brand_raw", "")),
                        "review_count": raw_item.get("review_count", 0),
                        "likes": raw_item.get("likes", 0),
                        "sold_range": raw_item.get("sold_range", str(raw_item.get("sold", 0))),
                        "rating": raw_item.get("rating", 0.0),
                    })
                    if len(items) >= top_n:
                        break

                page += 1

        return items[:top_n]

    def parse_response(self, raw_data: list[dict]) -> list[dict]:
        """Normalise TikTok raw items into standard format."""
        parsed: list[dict] = []
        for item in raw_data:
            parsed.append({
                "item_id": item.get("item_id", ""),
                "title": item.get("title", item.get("name", "")),
                "category": item.get("category", ""),
                "rank": item.get("rank", 0),
                "url": item.get("url", ""),
                "image_url": item.get("image_url", item.get("cover", "")),
                "price": item.get("price", 0),
                "promo_price": item.get("promo_price"),
                "currency": item.get("currency", "THB"),
                "brand_raw": item.get("brand_raw", item.get("brand", "")),
                "review_count": item.get("review_count", 0),
                "likes": item.get("likes", 0),
                "sold_range": item.get("sold_range", ""),
                "rating": item.get("rating", 0.0),
            })
        return parsed

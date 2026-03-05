"""Shopee platform adapter -- fetches top items from Shopee or stub data."""

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
    "th": "shopee.co.th",
    "sg": "shopee.sg",
    "my": "shopee.com.my",
    "id": "shopee.co.id",
    "ph": "shopee.ph",
    "vn": "shopee.vn",
}

CATEGORY_KEYWORD = {
    "personal_care": "personal care",
}


class ShopeeAdapter(BasePlatformAdapter):
    """Adapter for fetching top items from Shopee."""

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
        """Fetch top-N items from Shopee for *category* / *site*."""

        if self.use_stub:
            logger.info("Using stub data for shopee/%s", category)
            return self.stub_loader.load("shopee", category, self.event_date)

        # Live fetch attempt
        try:
            return await self._fetch_live(category, site, top_n)
        except Exception as exc:
            logger.error("Shopee live fetch failed: %s", exc)
            if self.stub_fallback:
                logger.info("Falling back to stub data for shopee/%s", category)
                return self.stub_loader.load("shopee", category, self.event_date)
            raise

    async def _fetch_live(
        self,
        category: str,
        site: str,
        top_n: int,
    ) -> list[dict]:
        """Paginated fetch from Shopee search API."""
        domain = SITE_DOMAIN.get(site, f"shopee.{site}")
        base_url = self.endpoint.base_url or f"https://{domain}/api/v4"
        search_url = f"{base_url}{self.endpoint.search_endpoint or '/search/search_items'}"

        keyword = CATEGORY_KEYWORD.get(category, category)
        items: list[dict] = []
        page_size = 60
        offset = 0

        async with httpx.AsyncClient(timeout=self.endpoint.timeout) as client:
            while len(items) < top_n:
                params = {
                    "by": "relevancy",
                    "keyword": keyword,
                    "limit": min(page_size, top_n - len(items)),
                    "newest": offset,
                    "order": "desc",
                    "page_type": "search",
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
                            "Shopee request failed (attempt %d/%d), retrying in %.1fs: %s",
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
                page_items = data.get("items", [])
                if not page_items:
                    break

                for rank_offset, raw_item in enumerate(page_items):
                    item_data = raw_item.get("item_basic", raw_item)
                    items.append({
                        "item_id": f"sh_{item_data.get('itemid', item_data.get('item_id', ''))}",
                        "title": item_data.get("name", item_data.get("title", "")),
                        "category": category,
                        "rank": len(items) + 1,
                        "url": f"https://{domain}/product/{item_data.get('itemid', '')}",
                        "image_url": f"https://cf.{domain}/file/{item_data.get('image', '')}",
                        "price": item_data.get("price", 0),
                        "promo_price": item_data.get("price_min", None),
                        "currency": "THB" if site == "th" else site.upper(),
                        "brand_raw": item_data.get("brand", ""),
                        "review_count": item_data.get("cmt_count", 0),
                        "sold_range": str(item_data.get("sold", 0)),
                        "rating": item_data.get("item_rating", {}).get(
                            "rating_star", 0.0
                        ) if isinstance(item_data.get("item_rating"), dict) else 0.0,
                    })
                    if len(items) >= top_n:
                        break

                offset += page_size

        return items[:top_n]

    def parse_response(self, raw_data: list[dict]) -> list[dict]:
        """Normalise Shopee raw items into standard format.

        If items already have the expected keys (e.g. from stub data) they are
        returned as-is.
        """
        parsed: list[dict] = []
        for item in raw_data:
            parsed.append({
                "item_id": item.get("item_id", ""),
                "title": item.get("title", item.get("name", "")),
                "category": item.get("category", ""),
                "rank": item.get("rank", 0),
                "url": item.get("url", ""),
                "image_url": item.get("image_url", ""),
                "price": item.get("price", 0),
                "promo_price": item.get("promo_price"),
                "currency": item.get("currency", "THB"),
                "brand_raw": item.get("brand_raw", ""),
                "review_count": item.get("review_count", 0),
                "sold_range": item.get("sold_range", ""),
                "rating": item.get("rating", 0.0),
            })
        return parsed

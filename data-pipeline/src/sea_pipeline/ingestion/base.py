"""Abstract base class for platform adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod


class BasePlatformAdapter(ABC):
    """Common interface that every platform scraper / API adapter must implement."""

    @abstractmethod
    async def fetch_top_items(
        self,
        category: str,
        site: str,
        top_n: int,
    ) -> list[dict]:
        """Fetch the top-N items for *category* on *site*.

        Returns a list of raw item dictionaries straight from the platform
        (or from stub data).
        """
        ...

    @abstractmethod
    def parse_response(self, raw_data: list[dict]) -> list[dict]:
        """Normalise the raw platform response into a uniform item format.

        The returned dicts must at least contain:
        item_id, title, rank, price, currency, brand_raw, url
        """
        ...

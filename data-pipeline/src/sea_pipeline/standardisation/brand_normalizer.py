"""Brand normalisation using a YAML dictionary of known brand aliases."""

from __future__ import annotations

import re
from pathlib import Path

import yaml


class BrandNormalizer:
    """Normalises raw brand strings to a canonical ``brand_std`` value.

    The dictionary YAML is expected to have the structure::

        aliases:
          key:
            std: "Canonical Name"
            variants: ["variant1", "variant2", ...]
    """

    def __init__(self, dictionary_path: str | Path = "data/brand_dictionary.yaml") -> None:
        self._lookup: dict[str, str] = {}
        self._load(dictionary_path)

    def _load(self, path: str | Path) -> None:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        aliases = data.get("aliases", {})
        for _key, entry in aliases.items():
            std = entry["std"]
            for variant in entry.get("variants", []):
                normalised = self.clean(variant)
                self._lookup[normalised] = std
            # Also add the std name itself
            self._lookup[self.clean(std)] = std

    @staticmethod
    def clean(text: str) -> str:
        """Lowercase, strip whitespace, and remove non-alphanumeric chars
        (preserving Thai and other unicode letters)."""
        text = text.strip().lower()
        # Keep unicode letters, digits, spaces, ampersand
        text = re.sub(r"[^\w\s&]", "", text, flags=re.UNICODE)
        # Collapse multiple spaces
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def normalize(self, brand_raw: str) -> str | None:
        """Return the standardised brand name, or ``None`` if unrecognised."""
        if not brand_raw:
            return None
        cleaned = self.clean(brand_raw)
        if cleaned in self._lookup:
            return self._lookup[cleaned]

        # Try substring match: check if any known variant is contained in the input
        for variant, std in self._lookup.items():
            if variant and variant in cleaned:
                return std

        return None

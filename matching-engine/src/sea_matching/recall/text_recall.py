"""Text similarity based candidate recall using TF-IDF or RapidFuzz."""

from __future__ import annotations

import re

from sea_matching.models.match_result import StandardizedItem


def _tokenize(text: str) -> list[str]:
    """Simple tokenization: lowercase, remove non-alphanumeric, split on whitespace."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u0e00-\u0e7f\s]", " ", text)  # Keep Thai chars
    return [t for t in text.split() if len(t) > 1]


class TextRecall:
    """Recall candidates based on title text similarity."""

    def __init__(self, method: str = "tfidf", min_similarity: float = 0.3):
        self.method = method
        self.min_similarity = min_similarity
        self._tfidf_matrix = None
        self._vectorizer = None
        self._target_items: list[StandardizedItem] = []

    def build_index(self, target_items: list[StandardizedItem]) -> None:
        """Build the text similarity index from target items."""
        self._target_items = target_items

        if self.method == "tfidf":
            self._build_tfidf_index(target_items)

    def _build_tfidf_index(self, items: list[StandardizedItem]) -> None:
        """Build TF-IDF matrix for target items."""
        from sklearn.feature_extraction.text import TfidfVectorizer

        titles = [item.title for item in items]
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            min_df=1,
            max_df=0.95,
            lowercase=True,
        )
        self._tfidf_matrix = self._vectorizer.fit_transform(titles)

    def recall(
        self, source_item: StandardizedItem, target_items: list[StandardizedItem] | None = None
    ) -> list[tuple[StandardizedItem, float]]:
        """Find candidates based on title similarity."""
        if self.method == "tfidf":
            return self._recall_tfidf(source_item)
        else:
            return self._recall_rapidfuzz(source_item, target_items or self._target_items)

    def _recall_tfidf(
        self, source_item: StandardizedItem
    ) -> list[tuple[StandardizedItem, float]]:
        """TF-IDF cosine similarity recall."""
        if self._vectorizer is None or self._tfidf_matrix is None:
            return []

        from sklearn.metrics.pairwise import cosine_similarity

        source_vec = self._vectorizer.transform([source_item.title])
        similarities = cosine_similarity(source_vec, self._tfidf_matrix).flatten()

        candidates = []
        for idx, sim in enumerate(similarities):
            if sim >= self.min_similarity:
                candidates.append((self._target_items[idx], float(sim)))

        return candidates

    def _recall_rapidfuzz(
        self, source_item: StandardizedItem, target_items: list[StandardizedItem]
    ) -> list[tuple[StandardizedItem, float]]:
        """RapidFuzz token-based similarity recall."""
        from rapidfuzz import fuzz

        candidates = []
        source_title = source_item.title.lower()

        for target in target_items:
            target_title = target.title.lower()
            score = fuzz.token_sort_ratio(source_title, target_title) / 100.0
            if score >= self.min_similarity:
                candidates.append((target, score))

        return candidates

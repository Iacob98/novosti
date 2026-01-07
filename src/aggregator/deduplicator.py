from typing import List, Set
from difflib import SequenceMatcher

from ..storage.models import RawArticle
from ..utils.logger import get_logger


logger = get_logger("deduplicator")


class Deduplicator:
    """Removes duplicate articles based on URL and title similarity."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold

    def deduplicate(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Remove duplicate articles."""
        if not articles:
            return []

        seen_urls: Set[str] = set()
        seen_titles: List[str] = []
        unique_articles: List[RawArticle] = []

        sorted_articles = sorted(
            articles,
            key=lambda a: a.published_at or a.fetched_at,
            reverse=True
        )

        for article in sorted_articles:
            if article.url in seen_urls:
                continue

            if self._is_similar_title(article.title, seen_titles):
                continue

            seen_urls.add(article.url)
            seen_titles.append(article.title)
            unique_articles.append(article)

        removed = len(articles) - len(unique_articles)
        if removed > 0:
            logger.info(f"Removed {removed} duplicate articles")

        return unique_articles

    def _is_similar_title(self, title: str, seen_titles: List[str]) -> bool:
        """Check if title is similar to any seen title."""
        title_lower = title.lower().strip()

        for seen in seen_titles:
            similarity = SequenceMatcher(
                None, title_lower, seen.lower().strip()
            ).ratio()

            if similarity >= self.similarity_threshold:
                return True

        return False

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison."""
        import re
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = ' '.join(title.split())
        return title

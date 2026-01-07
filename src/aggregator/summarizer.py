from typing import List, Dict

from ..storage.models import RawArticle
from ..llm.client import get_llm_client
from ..utils.logger import get_logger
from ..utils.config import get_region_info


logger = get_logger("summarizer")


class Summarizer:
    """Summarizes articles using LLM."""

    def __init__(self):
        self.llm = get_llm_client()

    async def summarize(
        self,
        articles: List[RawArticle],
        region: str
    ) -> Dict:
        """Create a summary of articles for a region."""
        if not articles:
            return {"key_topics": [], "stories": []}

        region_info = get_region_info(region)
        region_name = region_info.get("name_en", region)
        primary_lang = region_info.get("primary_language", "en")

        articles_text = self._format_articles_for_llm(articles)

        logger.info(f"Summarizing {len(articles)} articles for {region}")

        summary = await self.llm.summarize(
            articles_text=articles_text,
            region_name=region_name,
            language=primary_lang,
            max_words=500
        )

        return summary

    def _format_articles_for_llm(self, articles: List[RawArticle]) -> str:
        """Format articles as text for LLM input."""
        parts = []

        for i, article in enumerate(articles[:30], 1):
            source = article.source_name
            title = article.title
            desc = article.description[:500] if article.description else ""

            date_str = ""
            if article.published_at:
                date_str = article.published_at.strftime("%Y-%m-%d %H:%M")

            entry = f"""
---
Article {i}
Source: {source}
Date: {date_str}
Title: {title}
Summary: {desc}
---"""
            parts.append(entry)

        return "\n".join(parts)

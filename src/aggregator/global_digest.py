"""Global digest generator - creates a world news summary from all regions."""

from typing import Dict, List, Optional
from dataclasses import dataclass

from ..storage.models import RawArticle, ProcessedDigest
from ..storage.database import Database
from ..llm.client import LLMClient
from ..llm.prompts import get_global_digest_prompt
from ..aggregator.deduplicator import Deduplicator
from ..utils.logger import get_logger
from ..utils.timezone import get_time_period, now_in_timezone

import json


logger = get_logger("global_digest")


@dataclass
class GlobalEvent:
    """A globally significant news event."""
    headline: str
    summary: str
    regions_affected: List[str]
    importance: str


class GlobalDigestGenerator:
    """Generates a global digest from all regional news."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.llm = LLMClient()
        self.deduplicator = Deduplicator()

    async def generate(
        self,
        all_articles: Dict[str, List[RawArticle]]
    ) -> Optional[ProcessedDigest]:
        """
        Generate a global digest from articles across all regions.

        Args:
            all_articles: Dict mapping region -> list of articles

        Returns:
            ProcessedDigest for the global summary
        """
        total_articles = sum(len(arts) for arts in all_articles.values())
        if total_articles == 0:
            logger.warning("No articles to process for global digest")
            return None

        logger.info(f"Generating global digest from {total_articles} articles across {len(all_articles)} regions")

        # Flatten and deduplicate all articles
        all_flat = []
        for region, articles in all_articles.items():
            for article in articles:
                all_flat.append(article)

        unique_articles = self.deduplicator.deduplicate(all_flat)
        logger.info(f"After global deduplication: {len(unique_articles)} unique articles")

        # Prepare articles text for LLM (limit to top articles per region for efficiency)
        articles_by_region = self._group_by_region(unique_articles)
        articles_text = self._format_articles_for_llm(articles_by_region)

        # Generate global summary via LLM
        prompt = get_global_digest_prompt(articles_text, list(all_articles.keys()))

        try:
            messages = [
                {"role": "system", "content": "You are a professional global news analyst. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ]
            response = await self.llm.complete(messages=messages, max_tokens=2000, json_mode=True)
            summary = self._parse_global_response(response)
        except Exception as e:
            logger.error(f"LLM error generating global digest: {e}")
            return None

        # Create digest
        time_period = get_time_period(now_in_timezone("Europe/Berlin").hour)

        all_sources = set()
        for articles in all_articles.values():
            for a in articles:
                all_sources.add(a.source_name)

        digest = ProcessedDigest(
            region="global",
            region_name_ru="Мировой дайджест",
            summary_ru=self._format_global_summary(summary),
            key_topics=summary.get("key_topics", []),
            article_count=total_articles,
            sources_used=list(all_sources)[:10],
            article_ids=[a.id for a in unique_articles[:50]],
            time_period=time_period,
        )

        self.db.save_digest(digest)
        logger.info("Global digest generated successfully")

        return digest

    def _group_by_region(self, articles: List[RawArticle]) -> Dict[str, List[RawArticle]]:
        """Group articles by region."""
        grouped = {}
        for article in articles:
            if article.region not in grouped:
                grouped[article.region] = []
            grouped[article.region].append(article)
        return grouped

    def _format_articles_for_llm(
        self,
        articles_by_region: Dict[str, List[RawArticle]],
        max_per_region: int = 15
    ) -> str:
        """Format articles for LLM processing."""
        parts = []

        region_names = {
            "usa": "USA",
            "russia": "Russia",
            "europe": "Europe",
            "china": "China",
            "japan": "Japan",
            "india": "India",
            "middle_east": "Middle East",
            "latam": "Latin America"
        }

        for region, articles in articles_by_region.items():
            region_name = region_names.get(region, region.upper())
            parts.append(f"\n=== {region_name} ===")

            for article in articles[:max_per_region]:
                title = article.title[:200] if article.title else ""
                desc = article.description[:300] if article.description else ""
                source = article.source_name or "Unknown"
                parts.append(f"[{source}] {title}")
                if desc:
                    parts.append(f"   {desc}")

        return "\n".join(parts)

    def _parse_global_response(self, response: str) -> dict:
        """Parse LLM response for global digest."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            return json.loads(response.strip())
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using fallback")
            return {
                "key_topics": ["World Events"],
                "events": [
                    {
                        "headline": "Global News Summary",
                        "summary": response[:500],
                        "regions": ["global"],
                        "importance": "high"
                    }
                ]
            }

    def _format_global_summary(self, summary: dict) -> str:
        """Format the global summary into readable text."""
        parts = []

        region_names_ru = {
            "usa": "США",
            "russia": "Россия",
            "europe": "Европа",
            "china": "Китай",
            "japan": "Япония",
            "india": "Индия",
            "middle_east": "Ближний Восток",
            "latam": "Латинская Америка",
            "global": "Глобально"
        }

        for i, event in enumerate(summary.get("events", []), 1):
            headline = event.get("headline", "")
            text = event.get("summary", "")
            regions = event.get("regions", [])

            # Translate region codes to Russian
            regions_ru = [region_names_ru.get(r, r) for r in regions]
            regions_str = ", ".join(regions_ru) if regions_ru else ""

            parts.append(f"<b>{i}. {headline}</b>")
            parts.append(text)
            if regions_str:
                parts.append(f"<i>Регионы: {regions_str}</i>")
            parts.append("")

        return "\n".join(parts)

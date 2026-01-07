from typing import Optional, Dict, List, Tuple
from datetime import datetime

from ..storage.database import Database
from ..storage.models import ProcessedDigest, RawArticle
from ..utils.logger import get_logger
from ..utils.config import get_region_info
from ..utils.timezone import get_time_period, now_in_timezone

from .collector import Collector
from .deduplicator import Deduplicator
from .summarizer import Summarizer
from .translator import Translator
from .global_digest import GlobalDigestGenerator


logger = get_logger("pipeline")


class NewsPipeline:
    """Main pipeline for processing news from a region."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.collector = Collector(self.db)
        self.deduplicator = Deduplicator()
        self.summarizer = Summarizer()
        self.translator = Translator()
        self.global_generator = GlobalDigestGenerator(self.db)

    async def process_region(self, region: str) -> Optional[ProcessedDigest]:
        """Process news for a single region through the full pipeline."""
        logger.info(f"Starting pipeline for {region}")

        region_info = get_region_info(region)
        timezone = region_info.get("timezone", "UTC")
        primary_lang = region_info.get("primary_language", "en")
        region_name_ru = region_info.get("name_ru", region)

        articles = await self.collector.collect_and_store(region)

        if not articles:
            logger.warning(f"No articles found for {region}")
            return None

        logger.info(f"Collected {len(articles)} articles for {region}")

        unique_articles = self.deduplicator.deduplicate(articles)
        logger.info(f"After deduplication: {len(unique_articles)} articles")

        if not unique_articles:
            return None

        summary = await self.summarizer.summarize(unique_articles, region)

        if primary_lang != "ru":
            summary = await self.translator.translate_summary(
                summary, primary_lang
            )

        summary_text = self._format_summary_text(summary)

        region_time = now_in_timezone(timezone)
        time_period = get_time_period(region_time.hour)

        digest = ProcessedDigest(
            region=region,
            region_name_ru=region_name_ru,
            summary_ru=summary_text,
            key_topics=summary.get("key_topics", []),
            article_count=len(unique_articles),
            sources_used=list(set(a.source_name for a in unique_articles)),
            article_ids=[a.id for a in unique_articles],
            time_period=time_period,
        )

        self.db.save_digest(digest)
        self.db.mark_articles_processed([a.id for a in unique_articles])

        logger.info(f"Pipeline completed for {region}")
        return digest

    def _format_summary_text(self, summary: dict) -> str:
        """Format summary dict into readable text."""
        parts = []

        for i, story in enumerate(summary.get("stories", []), 1):
            headline = story.get("headline", "")
            text = story.get("summary", "")
            parts.append(f"<b>{i}. {headline}</b>\n{text}")

        return "\n\n".join(parts)

    async def collect_region_articles(self, region: str) -> List[RawArticle]:
        """Collect articles for a region without generating digest."""
        logger.info(f"Collecting articles for {region}")
        articles = await self.collector.collect_and_store(region)
        return articles or []

    async def process_all_regions(self, regions: list) -> dict:
        """Process all regions and return digests."""
        results = {}

        for region in regions:
            try:
                digest = await self.process_region(region)
                results[region] = digest
            except Exception as e:
                logger.error(f"Error processing {region}: {e}")
                results[region] = None

        return results

    async def process_all_with_global(
        self,
        regions: list
    ) -> Tuple[Optional[ProcessedDigest], Dict[str, Optional[ProcessedDigest]]]:
        """
        Process all regions and generate both global and regional digests.

        Returns:
            Tuple of (global_digest, regional_digests_dict)
        """
        logger.info(f"Starting full pipeline with global digest for {len(regions)} regions")

        # Step 1: Collect all articles from all regions
        all_articles: Dict[str, List[RawArticle]] = {}
        for region in regions:
            try:
                articles = await self.collect_region_articles(region)
                all_articles[region] = articles
                logger.info(f"Collected {len(articles)} articles from {region}")
            except Exception as e:
                logger.error(f"Error collecting from {region}: {e}")
                all_articles[region] = []

        total = sum(len(a) for a in all_articles.values())
        logger.info(f"Total articles collected: {total}")

        # Step 2: Generate global digest FIRST
        global_digest = None
        try:
            global_digest = await self.global_generator.generate(all_articles)
            if global_digest:
                logger.info("Global digest generated successfully")
        except Exception as e:
            logger.error(f"Error generating global digest: {e}")

        # Step 3: Generate regional digests
        regional_digests = {}
        for region in regions:
            try:
                articles = all_articles.get(region, [])
                if not articles:
                    regional_digests[region] = None
                    continue

                # Deduplicate and summarize
                unique_articles = self.deduplicator.deduplicate(articles)
                if not unique_articles:
                    regional_digests[region] = None
                    continue

                region_info = get_region_info(region)
                primary_lang = region_info.get("primary_language", "en")
                region_name_ru = region_info.get("name_ru", region)
                timezone = region_info.get("timezone", "UTC")

                summary = await self.summarizer.summarize(unique_articles, region)

                if primary_lang != "ru":
                    summary = await self.translator.translate_summary(summary, primary_lang)

                summary_text = self._format_summary_text(summary)
                region_time = now_in_timezone(timezone)
                time_period = get_time_period(region_time.hour)

                digest = ProcessedDigest(
                    region=region,
                    region_name_ru=region_name_ru,
                    summary_ru=summary_text,
                    key_topics=summary.get("key_topics", []),
                    article_count=len(unique_articles),
                    sources_used=list(set(a.source_name for a in unique_articles)),
                    article_ids=[a.id for a in unique_articles],
                    time_period=time_period,
                )

                self.db.save_digest(digest)
                self.db.mark_articles_processed([a.id for a in unique_articles])
                regional_digests[region] = digest
                logger.info(f"Regional digest for {region} completed")

            except Exception as e:
                logger.error(f"Error processing {region}: {e}")
                regional_digests[region] = None

        return global_digest, regional_digests

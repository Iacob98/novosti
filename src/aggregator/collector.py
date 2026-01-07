from typing import List, Dict
from datetime import datetime

from ..storage.database import Database
from ..storage.models import RawArticle
from ..parsers.regional_parser import fetch_region
from ..utils.logger import get_logger


logger = get_logger("collector")


class Collector:
    """Collects articles from parsers and storage."""

    def __init__(self, db: Database):
        self.db = db

    async def collect_fresh(self, region: str) -> List[RawArticle]:
        """Fetch fresh articles from sources and save to database."""
        logger.info(f"Fetching fresh articles for {region}")

        articles = await fetch_region(region)

        if articles:
            saved = self.db.save_articles(articles)
            logger.info(f"Saved {saved} new articles for {region}")

        return articles

    def collect_from_db(
        self,
        region: str,
        hours_back: int = 12,
        unprocessed_only: bool = True
    ) -> List[RawArticle]:
        """Collect articles from database."""
        return self.db.get_articles_for_region(
            region=region,
            hours_back=hours_back,
            unprocessed_only=unprocessed_only
        )

    async def collect_and_store(self, region: str) -> List[RawArticle]:
        """Collect fresh articles, store them, and return all unprocessed."""
        await self.collect_fresh(region)
        return self.collect_from_db(region)

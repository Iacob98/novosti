from abc import ABC, abstractmethod
from typing import List, Dict, Any
import asyncio

from ..storage.models import RawArticle
from ..utils.logger import get_logger
from ..utils.config import load_region_sources, get_region_info


class BaseParser(ABC):
    """Base class for all regional news parsers."""

    def __init__(self, region: str):
        self.region = region
        self.logger = get_logger(f"parser.{region}")
        self.region_info = get_region_info(region)
        self.sources_config = load_region_sources(region)
        self.rss_sources = self.sources_config.get("rss_sources", [])
        self.api_sources = self.sources_config.get("api_sources", [])

    @property
    def primary_language(self) -> str:
        """Get primary language for this region."""
        return self.region_info.get("primary_language", "en")

    @property
    def timezone(self) -> str:
        """Get timezone for this region."""
        return self.region_info.get("timezone", "UTC")

    @abstractmethod
    async def fetch(self) -> List[RawArticle]:
        """Fetch articles from all sources for this region."""
        pass

    @abstractmethod
    async def fetch_from_source(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch articles from a single source."""
        pass

    async def fetch_all_sources(self) -> List[RawArticle]:
        """Fetch from all RSS and API sources concurrently."""
        all_articles = []

        rss_tasks = [
            self.fetch_from_rss(source)
            for source in self.rss_sources
        ]

        api_tasks = [
            self.fetch_from_api(source)
            for source in self.api_sources
        ]

        results = await asyncio.gather(
            *rss_tasks, *api_tasks,
            return_exceptions=True
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Error fetching source: {result}")
            elif result:
                all_articles.extend(result)

        self.logger.info(
            f"Fetched {len(all_articles)} articles from {self.region}"
        )
        return all_articles

    async def fetch_from_rss(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch from RSS source. Override in subclass or use RSSParser."""
        return []

    async def fetch_from_api(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch from API source. Override in subclass."""
        return []

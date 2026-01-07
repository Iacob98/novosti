from typing import List, Dict, Any
import asyncio

from .base_parser import BaseParser
from .rss_parser import RSSParser
from ..storage.models import RawArticle


class RegionalParser(BaseParser):
    """Generic regional parser that uses RSS feeds and APIs."""

    def __init__(self, region: str):
        super().__init__(region)
        self.rss_parser = RSSParser()

    async def fetch(self) -> List[RawArticle]:
        """Fetch articles from all sources for this region."""
        return await self.fetch_all_sources()

    async def fetch_from_source(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch articles from a single source."""
        if "url" in source:
            return await self.fetch_from_rss(source)
        elif "api_name" in source:
            return await self.fetch_from_api(source)
        return []

    async def fetch_from_rss(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch from RSS source."""
        return await self.rss_parser.fetch_source(source, self.region)

    async def fetch_from_api(self, source: Dict[str, Any]) -> List[RawArticle]:
        """Fetch from News API source. To be implemented."""
        # TODO: Implement NewsAPI integration
        return []


def create_parser(region: str) -> RegionalParser:
    """Factory function to create a parser for a region."""
    return RegionalParser(region)


async def fetch_region(region: str) -> List[RawArticle]:
    """Convenience function to fetch all articles for a region."""
    parser = create_parser(region)
    return await parser.fetch()


async def fetch_all_regions(regions: List[str]) -> Dict[str, List[RawArticle]]:
    """Fetch articles from all specified regions concurrently."""
    tasks = {region: fetch_region(region) for region in regions}
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    return {
        region: result if not isinstance(result, Exception) else []
        for region, result in zip(tasks.keys(), results)
    }

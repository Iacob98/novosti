import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime

import feedparser
import httpx

from ..storage.models import RawArticle
from ..utils.logger import get_logger


logger = get_logger("rss_parser")


class RSSParser:
    """Parser for RSS/Atom feeds."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "NewsAggregator/1.0 (https://github.com/news-aggregator)"
        }

    async def fetch_feed(self, url: str) -> Optional[feedparser.FeedParserDict]:
        """Fetch and parse an RSS feed."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                return feedparser.parse(response.text)
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching feed: {url}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP error fetching feed {url}: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
        return None

    def parse_entry(
        self,
        entry: Dict[str, Any],
        source_name: str,
        source_url: str,
        region: str,
        language: str
    ) -> Optional[RawArticle]:
        """Parse a single feed entry into RawArticle."""
        try:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                return None

            description = ""
            if "summary" in entry:
                description = entry["summary"]
            elif "description" in entry:
                description = entry["description"]

            description = self._clean_html(description)

            content = None
            if "content" in entry and entry["content"]:
                content = entry["content"][0].get("value", "")
                content = self._clean_html(content)

            published_at = self._parse_date(entry)

            categories = []
            if "tags" in entry:
                categories = [tag.get("term", "") for tag in entry.get("tags", [])]
            elif "category" in entry:
                categories = [entry["category"]]

            return RawArticle(
                region=region,
                source_name=source_name,
                source_url=source_url,
                title=title,
                description=description[:1000] if description else "",
                content=content,
                url=link,
                published_at=published_at,
                language=language,
                categories=[c for c in categories if c][:5],
            )
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None

    def _parse_date(self, entry: Dict[str, Any]) -> Optional[datetime]:
        """Parse publication date from feed entry."""
        date_fields = ["published", "updated", "created"]

        for field in date_fields:
            if field in entry:
                try:
                    parsed = entry.get(f"{field}_parsed")
                    if parsed:
                        return datetime(*parsed[:6])
                except Exception:
                    pass

                try:
                    return parsedate_to_datetime(entry[field])
                except Exception:
                    pass

        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""

        import re
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        return text.strip()

    async def fetch_source(
        self,
        source: Dict[str, Any],
        region: str
    ) -> List[RawArticle]:
        """Fetch articles from a single RSS source."""
        url = source.get("url", "")
        name = source.get("name", "Unknown")
        language = source.get("language", "en")

        if not url:
            return []

        feed = await self.fetch_feed(url)
        if not feed or not feed.entries:
            logger.warning(f"No entries from {name}")
            return []

        articles = []
        for entry in feed.entries:
            article = self.parse_entry(
                entry=entry,
                source_name=name,
                source_url=url,
                region=region,
                language=language
            )
            if article:
                articles.append(article)

        logger.info(f"Parsed {len(articles)} articles from {name}")
        return articles

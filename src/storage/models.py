from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field
import uuid

from sqlalchemy import (
    Column, String, Text, DateTime, Integer, JSON, Boolean,
    create_engine, Index
)
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class RawArticleModel(Base):
    """Raw article from news source."""
    __tablename__ = "raw_articles"

    id = Column(String(36), primary_key=True)
    region = Column(String(20), index=True, nullable=False)
    source_name = Column(String(100), nullable=False)
    source_url = Column(String(500))
    title = Column(Text, nullable=False)
    description = Column(Text)
    content = Column(Text)
    url = Column(String(1000), unique=True, nullable=False)
    published_at = Column(DateTime, index=True)
    language = Column(String(10))
    categories = Column(JSON, default=list)
    fetched_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

    __table_args__ = (
        Index("idx_region_published", "region", "published_at"),
        Index("idx_region_processed", "region", "processed"),
    )


class DigestModel(Base):
    """Processed news digest."""
    __tablename__ = "digests"

    id = Column(String(36), primary_key=True)
    region = Column(String(20), index=True, nullable=False)
    region_name_ru = Column(String(50))
    summary_ru = Column(Text, nullable=False)
    key_topics = Column(JSON, default=list)
    article_count = Column(Integer, default=0)
    sources_used = Column(JSON, default=list)
    article_ids = Column(JSON, default=list)
    time_period = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime)


@dataclass
class RawArticle:
    """Data class for raw article."""
    region: str
    source_name: str
    title: str
    url: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_url: str = ""
    description: str = ""
    content: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str = "en"
    categories: List[str] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.utcnow)

    def to_model(self) -> RawArticleModel:
        """Convert to SQLAlchemy model."""
        return RawArticleModel(
            id=self.id,
            region=self.region,
            source_name=self.source_name,
            source_url=self.source_url,
            title=self.title,
            description=self.description,
            content=self.content,
            url=self.url,
            published_at=self.published_at,
            language=self.language,
            categories=self.categories,
            fetched_at=self.fetched_at,
        )

    @classmethod
    def from_model(cls, model: RawArticleModel) -> "RawArticle":
        """Create from SQLAlchemy model."""
        return cls(
            id=model.id,
            region=model.region,
            source_name=model.source_name,
            source_url=model.source_url or "",
            title=model.title,
            description=model.description or "",
            content=model.content,
            url=model.url,
            published_at=model.published_at,
            language=model.language or "en",
            categories=model.categories or [],
            fetched_at=model.fetched_at,
        )


@dataclass
class ProcessedDigest:
    """Data class for processed digest."""
    region: str
    summary_ru: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    region_name_ru: str = ""
    key_topics: List[str] = field(default_factory=list)
    article_count: int = 0
    sources_used: List[str] = field(default_factory=list)
    article_ids: List[str] = field(default_factory=list)
    time_period: str = "evening"
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

    def to_model(self) -> DigestModel:
        """Convert to SQLAlchemy model."""
        return DigestModel(
            id=self.id,
            region=self.region,
            region_name_ru=self.region_name_ru,
            summary_ru=self.summary_ru,
            key_topics=self.key_topics,
            article_count=self.article_count,
            sources_used=self.sources_used,
            article_ids=self.article_ids,
            time_period=self.time_period,
            created_at=self.created_at,
            sent_at=self.sent_at,
        )

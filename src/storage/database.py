from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, RawArticleModel, DigestModel, RawArticle, ProcessedDigest


class Database:
    """Database manager for news storage."""

    def __init__(self, db_path: str = "data/news.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def save_article(self, article: RawArticle) -> bool:
        """Save a raw article to database. Returns False if duplicate."""
        with self.get_session() as session:
            existing = session.query(RawArticleModel).filter(
                RawArticleModel.url == article.url
            ).first()

            if existing:
                return False

            session.add(article.to_model())
            session.commit()
            return True

    def save_articles(self, articles: List[RawArticle]) -> int:
        """Save multiple articles. Returns count of new articles saved."""
        saved = 0
        with self.get_session() as session:
            for article in articles:
                existing = session.query(RawArticleModel).filter(
                    RawArticleModel.url == article.url
                ).first()

                if not existing:
                    session.add(article.to_model())
                    saved += 1

            session.commit()
        return saved

    def get_articles_for_region(
        self,
        region: str,
        hours_back: int = 12,
        unprocessed_only: bool = True
    ) -> List[RawArticle]:
        """Get articles for a region within time window."""
        since = datetime.utcnow() - timedelta(hours=hours_back)

        with self.get_session() as session:
            query = session.query(RawArticleModel).filter(
                and_(
                    RawArticleModel.region == region,
                    RawArticleModel.fetched_at >= since
                )
            )

            if unprocessed_only:
                query = query.filter(RawArticleModel.processed == False)

            query = query.order_by(RawArticleModel.published_at.desc())
            models = query.all()

            return [RawArticle.from_model(m) for m in models]

    def mark_articles_processed(self, article_ids: List[str]) -> None:
        """Mark articles as processed."""
        with self.get_session() as session:
            session.query(RawArticleModel).filter(
                RawArticleModel.id.in_(article_ids)
            ).update({"processed": True}, synchronize_session=False)
            session.commit()

    def save_digest(self, digest: ProcessedDigest) -> None:
        """Save a processed digest."""
        with self.get_session() as session:
            session.add(digest.to_model())
            session.commit()

    def get_latest_digest(self, region: str) -> Optional[ProcessedDigest]:
        """Get the latest digest for a region."""
        with self.get_session() as session:
            model = session.query(DigestModel).filter(
                DigestModel.region == region
            ).order_by(DigestModel.created_at.desc()).first()

            if not model:
                return None

            return ProcessedDigest(
                id=model.id,
                region=model.region,
                region_name_ru=model.region_name_ru or "",
                summary_ru=model.summary_ru,
                key_topics=model.key_topics or [],
                article_count=model.article_count,
                sources_used=model.sources_used or [],
                article_ids=model.article_ids or [],
                time_period=model.time_period or "evening",
                created_at=model.created_at,
                sent_at=model.sent_at,
            )

    def mark_digest_sent(self, digest_id: str) -> None:
        """Mark digest as sent."""
        with self.get_session() as session:
            session.query(DigestModel).filter(
                DigestModel.id == digest_id
            ).update({"sent_at": datetime.utcnow()}, synchronize_session=False)
            session.commit()

    def cleanup_old_articles(self, days: int = 7) -> int:
        """Remove articles older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self.get_session() as session:
            count = session.query(RawArticleModel).filter(
                RawArticleModel.fetched_at < cutoff
            ).delete()
            session.commit()
            return count

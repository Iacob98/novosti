from datetime import datetime
from typing import List

from ..storage.models import ProcessedDigest
from ..utils.config import get_region_info
from ..utils.timezone import format_datetime_ru, get_time_period_ru


REGION_EMOJIS = {
    "global": "\U0001F30D",
    "usa": "\U0001F1FA\U0001F1F8",
    "china": "\U0001F1E8\U0001F1F3",
    "japan": "\U0001F1EF\U0001F1F5",
    "india": "\U0001F1EE\U0001F1F3",
    "europe": "\U0001F1EA\U0001F1FA",
    "middle_east": "\U0001F30D",
    "latam": "\U0001F30E",
    "russia": "\U0001F1F7\U0001F1FA"
}


class TelegramFormatter:
    """Formats digests for Telegram messages."""

    def __init__(self, max_length: int = 4096):
        self.max_length = max_length
        self.separator = "\n" + "\u2501" * 20 + "\n"

    def format_digest(self, digest: ProcessedDigest) -> str:
        """Format a single digest for Telegram."""
        emoji = REGION_EMOJIS.get(digest.region, "\U0001F4F0")
        region_name = digest.region_name_ru or digest.region
        period_name = get_time_period_ru(digest.time_period)
        date_str = format_datetime_ru(digest.created_at)

        header = f"{emoji} <b>{region_name} | {period_name}</b>\n"
        header += f"<i>{date_str} MSK</i>"

        topics_section = ""
        if digest.key_topics:
            topics_list = "\n".join([f"\u2022 {topic}" for topic in digest.key_topics[:5]])
            topics_section = f"\n\n\U0001F4CC <b>Ключевые темы:</b>\n{topics_list}"

        news_section = f"\n\n\U0001F4F0 <b>Главные события:</b>\n\n{digest.summary_ru}"

        stats = f"\n\n\U0001F4CA <b>Статистика:</b>\n"
        stats += f"\u2022 Источников: {len(digest.sources_used)} | "
        stats += f"Статей: {digest.article_count}"

        sources_str = ", ".join(digest.sources_used[:5])
        if len(digest.sources_used) > 5:
            sources_str += f" (+{len(digest.sources_used) - 5})"
        sources = f"\n\n<i>Источники: {sources_str}</i>"

        message = header + self.separator + topics_section + self.separator + news_section + self.separator + stats + sources

        if len(message) > self.max_length:
            message = self._truncate_message(message)

        return message

    def _truncate_message(self, message: str) -> str:
        """Truncate message to fit Telegram limits."""
        if len(message) <= self.max_length:
            return message

        truncated = message[:self.max_length - 50]
        last_newline = truncated.rfind('\n')
        if last_newline > self.max_length // 2:
            truncated = truncated[:last_newline]

        return truncated + "\n\n<i>... (сокращено)</i>"

    def format_multiple_digests(
        self,
        digests: List[ProcessedDigest]
    ) -> List[str]:
        """Format multiple digests as separate messages."""
        return [self.format_digest(d) for d in digests if d]

    def format_global_digest(self, digest: ProcessedDigest) -> str:
        """Format the global digest for Telegram."""
        emoji = "\U0001F30D"
        period_name = get_time_period_ru(digest.time_period)
        date_str = format_datetime_ru(digest.created_at)

        header = f"{emoji} <b>МИРОВОЙ ДАЙДЖЕСТ | {period_name}</b>\n"
        header += f"<i>{date_str}</i>"

        topics_section = ""
        if digest.key_topics:
            topics_list = "\n".join([f"\u2022 {topic}" for topic in digest.key_topics[:5]])
            topics_section = f"\n\n\U0001F4CC <b>Ключевые темы:</b>\n{topics_list}"

        news_section = f"\n\n\U0001F525 <b>ГЛАВНЫЕ МИРОВЫЕ СОБЫТИЯ:</b>\n\n{digest.summary_ru}"

        stats = f"\n\n\U0001F4CA <b>Статистика:</b>\n"
        stats += f"\u2022 Регионов: 8 | Статей: {digest.article_count}"

        sources_str = ", ".join(digest.sources_used[:8])
        if len(digest.sources_used) > 8:
            sources_str += f" (+{len(digest.sources_used) - 8})"
        sources = f"\n\n<i>Источники: {sources_str}</i>"

        message = header + self.separator + topics_section + self.separator + news_section + self.separator + stats + sources

        if len(message) > self.max_length:
            message = self._truncate_message(message)

        return message

    def format_error_message(self, region: str, error: str) -> str:
        """Format an error message."""
        emoji = REGION_EMOJIS.get(region, "\U0001F4F0")
        region_info = get_region_info(region)
        region_name = region_info.get("name_ru", region)

        return f"{emoji} <b>{region_name}</b>\n\n\u26A0\uFE0F Ошибка при обработке: {error}"

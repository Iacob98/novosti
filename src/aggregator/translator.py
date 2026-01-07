from typing import Dict, List

from ..llm.client import get_llm_client
from ..utils.logger import get_logger
from ..utils.config import get_region_info


logger = get_logger("translator")


class Translator:
    """Translates summaries to Russian using LLM."""

    def __init__(self):
        self.llm = get_llm_client()

    async def translate_summary(
        self,
        summary: Dict,
        source_language: str
    ) -> Dict:
        """Translate a summary dict to Russian."""
        if source_language == "ru":
            return summary

        translated_stories = []
        for story in summary.get("stories", []):
            headline = await self.llm.translate(
                text=story["headline"],
                source_language=source_language,
                target_language="ru"
            )
            story_summary = await self.llm.translate(
                text=story["summary"],
                source_language=source_language,
                target_language="ru"
            )
            translated_stories.append({
                "headline": headline.strip(),
                "summary": story_summary.strip()
            })

        translated_topics = []
        for topic in summary.get("key_topics", []):
            translated = await self.llm.translate(
                text=topic,
                source_language=source_language,
                target_language="ru"
            )
            translated_topics.append(translated.strip())

        return {
            "key_topics": translated_topics,
            "stories": translated_stories
        }

    async def translate_to_russian(
        self,
        text: str,
        source_language: str
    ) -> str:
        """Translate text to Russian."""
        if source_language == "ru":
            return text

        logger.info(f"Translating from {source_language} to Russian")
        return await self.llm.translate(
            text=text,
            source_language=source_language,
            target_language="ru"
        )

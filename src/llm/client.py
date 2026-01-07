from typing import List, Dict, Optional
import json

from openai import AsyncOpenAI

from ..utils.logger import get_logger
from ..utils.config import get_settings, get_config


logger = get_logger("llm_client")


class LLMClient:
    """Client for OpenRouter API (OpenAI-compatible)."""

    def __init__(self):
        settings = get_settings()
        config = get_config()

        self.client = AsyncOpenAI(
            base_url=config["llm"]["base_url"],
            api_key=settings.openrouter_api_key,
        )

        self.default_model = config["llm"]["default_model"]
        self.fallback_model = config["llm"]["fallback_model"]
        self.temperature = config["llm"]["temperature"]

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
        json_mode: bool = False
    ) -> str:
        """Send a completion request to the LLM."""
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.temperature

        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM error with {model}: {e}")

            if model != self.fallback_model:
                logger.info(f"Trying fallback model: {self.fallback_model}")
                return await self.complete(
                    messages=messages,
                    model=self.fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode
                )
            raise

    async def summarize(
        self,
        articles_text: str,
        region_name: str,
        language: str = "en",
        max_words: int = 500
    ) -> Dict:
        """Summarize news articles and extract key topics."""
        from .prompts import get_summarization_prompt

        prompt = get_summarization_prompt(
            articles_text=articles_text,
            region_name=region_name,
            language=language,
            max_words=max_words
        )

        messages = [
            {"role": "system", "content": "You are a professional news analyst. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        config = get_config()
        response = await self.complete(
            messages=messages,
            max_tokens=config["llm"]["max_tokens_summary"],
            json_mode=True
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response[:200]}")
            return {
                "key_topics": [],
                "stories": [{"headline": "Error", "summary": response[:500]}]
            }

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str = "ru"
    ) -> str:
        """Translate text to target language."""
        from .prompts import get_translation_prompt

        prompt = get_translation_prompt(
            text=text,
            source_language=source_language,
            target_language=target_language
        )

        messages = [
            {"role": "system", "content": "You are a professional translator. Translate accurately while maintaining natural language flow."},
            {"role": "user", "content": prompt}
        ]

        config = get_config()
        return await self.complete(
            messages=messages,
            max_tokens=config["llm"]["max_tokens_translation"]
        )


_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client

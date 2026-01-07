"""LLM prompts for news summarization and translation."""


LANGUAGE_NAMES = {
    "en": "English",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "de": "German",
    "es": "Spanish",
    "pt": "Portuguese",
    "ar": "Arabic",
    "hi": "Hindi",
    "fr": "French",
}


def get_summarization_prompt(
    articles_text: str,
    region_name: str,
    language: str = "en",
    max_words: int = 500
) -> str:
    """Generate prompt for news summarization."""
    output_lang = LANGUAGE_NAMES.get(language, "English")

    return f"""Analyze the following news articles from {region_name} and create a structured summary.

ARTICLES:
{articles_text}

INSTRUCTIONS:
1. Identify the 3-5 most important and significant news stories
2. For each story, provide:
   - A clear, informative headline
   - A 2-3 sentence summary with key facts, numbers, and context
3. Extract 3-5 key topics/themes covered across all articles
4. Be objective and factual - present information without bias
5. Focus on events with real impact or significance
6. Total summary should be under {max_words} words

OUTPUT FORMAT (respond with valid JSON only):
{{
  "key_topics": ["Topic 1", "Topic 2", "Topic 3"],
  "stories": [
    {{
      "headline": "Clear headline describing the event",
      "summary": "2-3 sentence summary with key facts and context."
    }},
    {{
      "headline": "Second important story",
      "summary": "Summary of the second story."
    }}
  ]
}}

Write all content in {output_lang}."""


def get_translation_prompt(
    text: str,
    source_language: str,
    target_language: str = "ru"
) -> str:
    """Generate prompt for translation."""
    source_name = LANGUAGE_NAMES.get(source_language, source_language)
    target_name = LANGUAGE_NAMES.get(target_language, target_language)

    return f"""Translate the following text from {source_name} to {target_name}.

TEXT TO TRANSLATE:
{text}

REQUIREMENTS:
1. Preserve the exact meaning and tone of the original
2. Use natural, fluent {target_name} language
3. Keep proper nouns (names, organizations, places) recognizable
4. Maintain formatting (numbered lists, paragraphs, etc.)
5. Do not add explanations or commentary

OUTPUT: Only the translated text, nothing else."""


def get_digest_formatting_prompt(
    summaries: dict,
    region_name_ru: str
) -> str:
    """Generate prompt for final digest formatting."""
    return f"""Format the following news summary for {region_name_ru} into a clean, readable digest.

SUMMARY DATA:
{summaries}

FORMAT REQUIREMENTS:
1. Start with key topics as bullet points
2. Present each story with a bold headline followed by its summary
3. Use clear paragraph separation
4. Keep the language concise and informative
5. Output should be ready to send as a Telegram message

OUTPUT: Formatted text in Russian, ready for Telegram (HTML formatting allowed: <b>, <i>, etc.)"""


def get_global_digest_prompt(articles_text: str, regions: list) -> str:
    """Generate prompt for global news digest."""
    regions_str = ", ".join(regions)

    return f"""Analyze news from around the world and identify the 5-7 MOST IMPORTANT global events.

REGIONS COVERED: {regions_str}

NEWS ARTICLES:
{articles_text}

IMPORTANCE CRITERIA (prioritize in this order):
1. Geopolitical impact - events affecting international relations
2. Economic consequences - major market moves, trade, financial crises
3. Humanitarian significance - conflicts, disasters, health crises
4. Technological breakthroughs - major innovations affecting multiple countries
5. Environmental events - climate, natural disasters with global impact

CRITICAL RULES:
- If the SAME event is covered by multiple regions, combine into ONE entry
- List which regions are affected or covering each event
- Focus on FACTS, avoid repetition
- Only include truly significant world events, not local news
- Write summaries in Russian

OUTPUT FORMAT (respond with valid JSON only):
{{
  "key_topics": ["Геополитика", "Экономика", "Тема 3"],
  "events": [
    {{
      "headline": "Заголовок на русском языке",
      "summary": "Краткое описание события в 2-3 предложениях с ключевыми фактами.",
      "regions": ["usa", "europe", "china"],
      "importance": "high"
    }},
    {{
      "headline": "Второе важное событие",
      "summary": "Описание второго события.",
      "regions": ["middle_east"],
      "importance": "high"
    }}
  ]
}}

IMPORTANT: All text must be in Russian. Respond ONLY with valid JSON."""

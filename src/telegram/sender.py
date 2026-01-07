import asyncio
from typing import List, Optional

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from ..storage.models import ProcessedDigest
from ..storage.database import Database
from ..utils.logger import get_logger
from ..utils.config import get_settings, get_config

from .formatter import TelegramFormatter


logger = get_logger("telegram_sender")


class TelegramSender:
    """Sends news digests to Telegram."""

    def __init__(self, db: Optional[Database] = None):
        settings = get_settings()
        config = get_config()

        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_ids = settings.get_chat_ids()  # Support multiple users
        self.formatter = TelegramFormatter()
        self.db = db or Database()

        self.retry_attempts = config["telegram"]["retry_attempts"]
        self.retry_delay = config["telegram"]["retry_delay_seconds"]

    async def send_digest(self, digest: ProcessedDigest) -> bool:
        """Send a single digest to Telegram."""
        message = self.formatter.format_digest(digest)
        success = await self._send_message(message)

        if success:
            self.db.mark_digest_sent(digest.id)
            logger.info(f"Sent digest for {digest.region}")

        return success

    async def send_global_digest(self, digest: ProcessedDigest) -> bool:
        """Send the global digest to Telegram."""
        message = self.formatter.format_global_digest(digest)
        success = await self._send_message(message)

        if success:
            self.db.mark_digest_sent(digest.id)
            logger.info("Sent global digest")

        return success

    async def send_digests(
        self,
        digests: List[ProcessedDigest],
        delay_between: float = 2.0
    ) -> dict:
        """Send multiple digests with delay between each."""
        results = {}

        for digest in digests:
            if digest:
                results[digest.region] = await self.send_digest(digest)
                await asyncio.sleep(delay_between)

        return results

    async def _send_message(self, text: str) -> bool:
        """Send a message to all configured chat IDs with retry logic."""
        if not self.chat_ids:
            logger.error("No chat IDs configured")
            return False

        all_success = True
        for chat_id in self.chat_ids:
            success = await self._send_to_chat(text, chat_id)
            if not success:
                all_success = False

        return all_success

    async def _send_to_chat(self, text: str, chat_id: str) -> bool:
        """Send a message to a single chat ID with retry logic."""
        for attempt in range(self.retry_attempts):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
                return True

            except TelegramError as e:
                logger.error(f"Telegram error for {chat_id} (attempt {attempt + 1}): {e}")

                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return False

            except Exception as e:
                logger.error(f"Unexpected error sending to {chat_id}: {e}")
                return False

        return False

    async def send_status_message(self, text: str) -> bool:
        """Send a status/info message."""
        return await self._send_message(text)

    async def test_connection(self) -> bool:
        """Test Telegram bot connection."""
        try:
            me = await self.bot.get_me()
            logger.info(f"Connected to Telegram as @{me.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False

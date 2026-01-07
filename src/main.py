#!/usr/bin/env python3
"""
World News Aggregator Bot
Main entry point for the news aggregation system.
"""

import asyncio
import argparse
import signal
import sys
from typing import Optional

from .utils.logger import setup_logger, get_logger
from .utils.config import get_config, get_settings
from .storage.database import Database
from .aggregator.pipeline import NewsPipeline
from .telegram.sender import TelegramSender
from .scheduler.cron_manager import NewsScheduler


logger: Optional[get_logger] = None


async def process_and_send_news():
    """Main task: process all regions and send to Telegram."""
    global logger
    logger.info("Starting news processing cycle")

    config = get_config()
    regions = config.get("regions", [])

    db = Database()
    pipeline = NewsPipeline(db)
    sender = TelegramSender(db)

    # Process all regions and get global + regional digests
    global_digest, regional_digests = await pipeline.process_all_with_global(regions)

    sent_count = 0
    total_count = 0

    # Send GLOBAL digest FIRST
    if global_digest:
        total_count += 1
        success = await sender.send_global_digest(global_digest)
        if success:
            sent_count += 1
            logger.info("Global digest sent successfully")

    # Then send regional digests in order
    region_order = ["russia", "usa", "europe", "china", "japan", "india", "middle_east", "latam"]
    for region in region_order:
        if region in regional_digests and regional_digests[region]:
            total_count += 1
            success = await sender.send_digest(regional_digests[region])
            if success:
                sent_count += 1

    logger.info(f"Sent {sent_count}/{total_count} digests (1 global + {total_count - 1} regional)")
    logger.info("News processing cycle completed")


async def process_single_region(region: str):
    """Process and send news for a single region."""
    db = Database()
    pipeline = NewsPipeline(db)
    sender = TelegramSender(db)

    digest = await pipeline.process_region(region)

    if digest:
        success = await sender.send_digest(digest)
        return success
    return False


async def run_once():
    """Run a single news processing cycle."""
    await process_and_send_news()


async def run_scheduled():
    """Run the scheduler for continuous operation."""
    global logger

    scheduler = NewsScheduler()

    scheduler.add_news_jobs(process_and_send_news)

    scheduler.start()

    logger.info("Bot is running. Press Ctrl+C to stop.")

    stop_event = asyncio.Event()

    def handle_signal(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: handle_signal(s))

    await stop_event.wait()

    scheduler.stop()
    logger.info("Bot stopped")


async def test_telegram():
    """Test Telegram connection."""
    sender = TelegramSender()
    if await sender.test_connection():
        print("Telegram connection successful!")
        return True
    else:
        print("Telegram connection failed!")
        return False


async def test_rss(region: str = "usa"):
    """Test RSS parsing for a region."""
    from .parsers.regional_parser import fetch_region

    print(f"Testing RSS parsing for {region}...")
    articles = await fetch_region(region)
    print(f"Fetched {len(articles)} articles")

    for article in articles[:5]:
        print(f"\n- {article.source_name}: {article.title[:60]}...")

    return len(articles) > 0


def main():
    """Main entry point."""
    global logger

    parser = argparse.ArgumentParser(
        description="World News Aggregator Bot"
    )
    parser.add_argument(
        "command",
        choices=["run", "once", "test-telegram", "test-rss", "process"],
        help="Command to execute"
    )
    parser.add_argument(
        "--region",
        default="usa",
        help="Region to process (for 'process' and 'test-rss' commands)"
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Override log level"
    )

    args = parser.parse_args()

    settings = get_settings()
    log_level = args.log_level or settings.log_level
    logger = setup_logger(log_level=log_level)

    logger.info(f"Starting World News Aggregator - command: {args.command}")

    if args.command == "run":
        asyncio.run(run_scheduled())

    elif args.command == "once":
        asyncio.run(run_once())

    elif args.command == "test-telegram":
        success = asyncio.run(test_telegram())
        sys.exit(0 if success else 1)

    elif args.command == "test-rss":
        success = asyncio.run(test_rss(args.region))
        sys.exit(0 if success else 1)

    elif args.command == "process":
        success = asyncio.run(process_single_region(args.region))
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

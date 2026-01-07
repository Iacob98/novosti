#!/bin/bash

# World News Aggregator Bot - Run Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/.installed
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Run the bot with provided command
case "${1:-help}" in
    run)
        echo "Starting bot in scheduled mode..."
        python -m src.main run
        ;;
    once)
        echo "Running single news cycle..."
        python -m src.main once
        ;;
    test-telegram)
        echo "Testing Telegram connection..."
        python -m src.main test-telegram
        ;;
    test-rss)
        REGION="${2:-usa}"
        echo "Testing RSS parsing for $REGION..."
        python -m src.main test-rss --region "$REGION"
        ;;
    process)
        REGION="${2:-usa}"
        echo "Processing region $REGION..."
        python -m src.main process --region "$REGION"
        ;;
    help|*)
        echo "World News Aggregator Bot"
        echo ""
        echo "Usage: ./run.sh <command> [options]"
        echo ""
        echo "Commands:"
        echo "  run           Start bot in scheduled mode (runs continuously)"
        echo "  once          Run a single news processing cycle"
        echo "  test-telegram Test Telegram bot connection"
        echo "  test-rss      Test RSS parsing (default: usa)"
        echo "  process       Process a single region (default: usa)"
        echo "  help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run.sh run              # Start scheduled bot"
        echo "  ./run.sh once             # Run once and exit"
        echo "  ./run.sh test-rss russia  # Test RSS for Russia"
        echo "  ./run.sh process europe   # Process Europe region"
        ;;
esac

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY config/ ./config/
COPY src/ ./src/
COPY .env .

# Create data directory
RUN mkdir -p data/logs

# Set environment
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# Run bot
CMD ["python", "-m", "src.main", "run"]

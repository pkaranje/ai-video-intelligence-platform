FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/services/extractor

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY libs/shared ./libs/shared/

COPY services/extractor/pyproject.toml ./services/extractor/
WORKDIR /app/services/extractor
RUN uv sync --no-dev

COPY services/extractor/extractor ./extractor/

CMD ["uv", "run", "dramatiq", "extractor.main", "--processes", "1", "--threads", "4"]

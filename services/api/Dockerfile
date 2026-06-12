FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

RUN pip install uv

# Copy shared lib
COPY libs/shared ./libs/shared/

# Copy only pyproject.toml first for dependency caching
COPY services/api/pyproject.toml ./services/api/pyproject.toml

WORKDIR /app/services/api

# Install deps into venv
RUN uv sync --no-dev

# Copy source AFTER venv is built — only copy the package, not the whole dir
COPY services/api/api ./api/
COPY services/api/alembic ./alembic/
COPY services/api/alembic.ini ./alembic.ini

ENV PATH="/app/services/api/.venv/bin:$PATH"
ENV PYTHONPATH="/app/services/api"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

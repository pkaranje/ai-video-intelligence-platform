FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY libs/shared ./libs/shared/
COPY services/api/pyproject.toml ./services/api/
COPY services/api/ ./services/api/

WORKDIR /app/services/api

RUN uv sync --no-dev

ENV PATH="/app/services/api/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

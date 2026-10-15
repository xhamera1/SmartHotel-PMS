# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY app ./app
COPY domain ./domain
COPY ml ./ml
COPY fixtures ./fixtures
COPY migrations ./migrations
COPY alembic.ini ./

ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8081

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8081"]

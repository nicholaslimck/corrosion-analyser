# Builder image
FROM python:3.11 as builder

RUN pip install poetry==1.8.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# Runtime image
FROM python:3.11-slim as runtime

RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY src ./src

RUN mkdir -p /tmp/corrosion-analyser-cache /tmp/corrosion-analyser-flask-cache \
    && chown -R appuser:appuser /app /tmp/corrosion-analyser-cache /tmp/corrosion-analyser-flask-cache

USER appuser
ENV DOCKER=true

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/')" || exit 1

ENTRYPOINT ["python", "-m", "src.app"]

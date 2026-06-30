FROM python:3.12-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir poetry==2.2.1

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

FROM python:3.12-slim AS users

RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser ./app/core ./app/core
COPY --chown=appuser:appuser ./app/outbox ./app/outbox
COPY --chown=appuser:appuser ./app/users ./app/users

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.users.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.12-slim AS transactions

RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser ./app/core ./app/core
COPY --chown=appuser:appuser ./app/outbox ./app/outbox
COPY --chown=appuser:appuser ./app/users ./app/users
COPY --chown=appuser:appuser ./app/transactions ./app/transactions

USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.transactions.main:app", "--host", "0.0.0.0", "--port", "8001"]
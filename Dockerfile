FROM python:3.12-slim as builder

WORKDIR /build

RUN pip install poetry==2.2.1

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

FROM python:3.12-slim as runtime

RUN useradd -m appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY --chown=appuser:appuser ./app .

USER appuser

EXPOSE 7999

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7999"]
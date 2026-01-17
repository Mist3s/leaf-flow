FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY pyproject.toml ./
COPY README.md ./
COPY src ./src
RUN pip install --upgrade pip && pip install .

# создать пользователя + директории + права
RUN useradd -m appuser \
 && mkdir -p /app/static/images \
 && chown -R appuser:appuser /app

USER appuser

CMD ["gunicorn", "leaf_flow.app:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
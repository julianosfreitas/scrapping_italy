# Scraper — coleta do Radar (intervalo) + curadoria da newsletter (cron 08h30).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# o scheduler importa app.core.decoradores da api, então as duas árvores entram
COPY api/pyproject.toml ./api/
COPY api/app ./api/app
RUN pip install --no-cache-dir ./api

COPY scraper/requirements.txt ./scraper/
RUN pip install --no-cache-dir -r scraper/requirements.txt

COPY scraper ./scraper

ENV PYTHONPATH=/app:/app/api

RUN useradd --create-home --uid 10002 ponte && chown -R ponte:ponte /app
USER ponte

CMD ["python", "-m", "scraper.scheduler"]

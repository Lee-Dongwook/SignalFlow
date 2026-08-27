FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV SIGNALFLOW_DB_PATH=/app/data/signalflow.db

COPY apps/backend_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/backend_api/ ./apps/backend_api/
COPY apps/dlq_healing_agent/ ./apps/dlq_healing_agent/

EXPOSE 8001

CMD ["sh", "-c", "uvicorn apps.backend_api.main:app --host 0.0.0.0 --port ${PORT:-8001}"]

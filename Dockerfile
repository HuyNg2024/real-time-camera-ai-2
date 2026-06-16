FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir fastapi uvicorn psycopg2-binary pydantic

COPY camera_api.py /app/camera_api.py
COPY sql /app/sql

RUN mkdir -p /app/runs/postgres_snapshots

EXPOSE 8000

CMD ["uvicorn", "camera_api:app", "--host", "0.0.0.0", "--port", "8000"]

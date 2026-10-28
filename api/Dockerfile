FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite lives in the mounted volume, shared by the api and worker services.
VOLUME ["/app/data"]

EXPOSE 8000

CMD ["sh", "-c", "python cli.py init-db && uvicorn main:app --host 0.0.0.0 --port 8000 --proxy-headers"]

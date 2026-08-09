FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Force rebuild: 2026-08-09
COPY . .

RUN mkdir -p data/cache data/documents

EXPOSE 8080

CMD ["python", "run.py"]

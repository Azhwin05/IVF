# ============================================================
# Multi-stage build — per ARCHITECTURE.md §5: minimal final image,
# non-root user, no build toolchain left in the runtime layer.
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.12-slim AS runtime

# Runtime-only system deps:
#   libpq5             - psycopg2
#   curl               - the healthcheck
#   tesseract-ocr      - OCR for scanned / image laboratory reports
#                        (pytesseract shells out to the `tesseract` binary;
#                        with it absent the extraction pipeline degrades
#                        safely and flags the report instead of guessing)
#   tesseract-ocr-eng  - English trained data (--no-install-recommends would
#                        otherwise skip it, leaving `tesseract` unusable)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 archana && useradd --uid 1000 --gid archana --shell /bin/bash --create-home archana

WORKDIR /app
COPY --from=builder /root/.local /home/archana/.local
COPY --chown=archana:archana . .

ENV PATH=/home/archana/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN chmod +x scripts/backup.sh

USER archana

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

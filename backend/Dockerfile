FROM python:3.12-slim

# tesseract-ocr + poppler-utils needed for payslip OCR/PDF parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

# --workers kept low by default: this targets a small self-hosted VPS,
# not an autoscaled cluster. Bump via env/Coolify service settings if
# the host has spare cores.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

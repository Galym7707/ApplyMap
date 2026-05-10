FROM python:3.11-slim

WORKDIR /app

# OCR runtime: tesseract (eng/rus/kaz) + poppler for pdf2image + libGL for opencv-headless.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      tesseract-ocr-eng \
      tesseract-ocr-rus \
      tesseract-ocr-kaz \
      poppler-utils \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

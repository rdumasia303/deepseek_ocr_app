# Backend Dockerfile - FastAPI + DeepSeek-OCR
FROM nvcr.io/nvidia/pytorch:25.09-py3

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy backend code
COPY main.py .
COPY pdf_utils.py .

EXPOSE 8000

# Use uvicorn with reasonable workers for GPU workload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

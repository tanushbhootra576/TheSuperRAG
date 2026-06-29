FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required by any python package
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1
ENV HF_HOME=/app/.cache/huggingface

# Pre-download the embedding models so it doesn't block the server startup on Render
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2'); from langchain_qdrant import FastEmbedSparse; FastEmbedSparse(model_name='Qdrant/bm25')"

# Expose port
EXPOSE 8000

# Start server using Uvicorn directly, respecting the PORT env var (defaults to 8000)
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4"]

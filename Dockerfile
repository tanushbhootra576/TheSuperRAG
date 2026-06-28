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

# Expose port
EXPOSE 8000

# Start server using Uvicorn directly
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

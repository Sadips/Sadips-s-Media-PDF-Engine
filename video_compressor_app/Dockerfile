# ==============================================================================
# Google Antigravity - Production Dockerfile for Media & PDF Compressor
# ==============================================================================

FROM python:3.11-slim

# Install FFmpeg and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn waitress

# Copy application files
COPY . .

# Environment variables
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Run with Gunicorn WSGI Server (2 worker processes, 300s timeout for large video processing)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "300", "app:app"]

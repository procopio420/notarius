# Multi-stage build for Notarius API
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/packages \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
   # WeasyPrint dependencies - comprehensive set
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi8 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libgtk-3-0 \
    libcairo-gobject2 \
    libpangoft2-1.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-test.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Development stage
FROM base as development

# Install development dependencies
RUN pip install -r requirements-test.txt

# Copy application code
COPY . .

# Set up MinIO and collect static files during build
# Disable S3 during build to avoid MinIO connection errors
ENV USE_S3=False
RUN python manage.py setup_minio_build

# Create non-root user
RUN useradd --create-home --shell /bin/bash notarius && \
    chown -R notarius:notarius /app
USER notarius

# Expose port
EXPOSE 8000

# Default command
CMD ["sh", "-c", "python manage.py setup_minio && uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload"]

# Production stage
FROM base as production

# Install production dependencies only
RUN pip install gunicorn

# Copy application code
COPY . .

# Set up MinIO and collect static files during build
# Disable S3 during build to avoid MinIO connection errors
ENV USE_S3=False
RUN python manage.py setup_minio_build

# Create non-root user
RUN useradd --create-home --shell /bin/bash notarius && \
    chown -R notarius:notarius /app
USER notarius

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command
CMD ["sh", "-c", "python manage.py setup_minio && gunicorn config.asgi:application --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker"]


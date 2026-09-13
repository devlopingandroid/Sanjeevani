# ==========================================
# SANJEEVNI Backend Production Dockerfile
# Multi-stage, non-root user, slim runtime
# ==========================================

FROM python:3.12-slim as base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies (build-essential, libpq for postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source
COPY . .

# Create non-root user and assign permissions
RUN useradd -m -u 1001 sanjeevni && \
    chown -R sanjeevni:sanjeevni /app

USER sanjeevni

EXPOSE 8000

# Healthcheck probe using liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

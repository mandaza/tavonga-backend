# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN addgroup --system --gid 1001 django && \
    adduser --system --uid 1001 django

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p logs staticfiles media && \
    chown -R django:django /app

# Switch to non-root user
USER django

# Collect static files
RUN python manage.py collectstatic --noinput

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check --database || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120", "core.wsgi:application"] 
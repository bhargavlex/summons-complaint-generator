# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Container-level health check - checks if FastAPI server is responding
# This allows Docker to mark the container as healthy/unhealthy
# Works with or without a /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(2); result=s.connect_ex(('localhost', 8000)); s.close(); exit(0) if result == 0 else exit(1)" || exit 1

# Run the application
# Use --reload only for development. For production, remove --reload and add --workers 4
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

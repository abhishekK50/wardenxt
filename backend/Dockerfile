# WardenXT Backend Dockerfile
# Optimized for Railway deployment

FROM python:3.11-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy incident data from data-generation (sibling directory)
# This will be handled by the build context

# Create directories for runtime data
RUN mkdir -p /app/data /app/logs /app/data-generation/output

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_ENV=production

# Railway sets PORT dynamically
ENV PORT=8000

# Expose port (Railway overrides this)
EXPOSE $PORT

# Start command - uses PORT env var
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

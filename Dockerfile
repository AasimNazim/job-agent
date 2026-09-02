FROM python:3.12-slim

# Install system dependencies (e.g., for sqlite, pdf processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e .

# Copy source code (excluding .dockerignore files)
COPY . .

# Ensure entrypoint is executable
RUN chmod +x /app/entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

# Healthcheck hitting the unprotected /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

# Builder stage
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .

# Install dependencies into a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install curl for health checks and useradd for non-root execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

# Copy virtual environment and set PATH
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy source code and tests with correct ownership
COPY --chown=appuser:appuser app/ ./app
COPY --chown=appuser:appuser tests/ ./tests
COPY --chown=appuser:appuser scripts/ ./scripts

EXPOSE 8000

USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

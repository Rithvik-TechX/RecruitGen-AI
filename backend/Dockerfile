# ──────────────────────────────────────────────────────────
# RecruitmentGen AI — Backend Dockerfile
# Multi-stage build · Python 3.12 · Non-root user
# ──────────────────────────────────────────────────────────

# ── Stage 1: Builder ────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /tmp

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Stage 1: Install CPU-only PyTorch first (--index-url = exclusive, no CUDA)
RUN pip install --no-cache-dir --prefix=/install \
    --timeout 120 \
    torch torchvision --index-url https://download.pytorch.org/whl/cpu
# Stage 2: Install remaining deps (torch already satisfied from above)
RUN PYTHONPATH=/install/lib/python3.12/site-packages pip install --no-cache-dir --prefix=/install \
    --timeout 120 \
    -r requirements.txt

# ── Stage 2: Runtime ────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Own files by appuser
RUN chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

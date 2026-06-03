FROM python:3.11-slim

# Install system build dependencies + OpenBLAS (critical for llama-cpp-python CPU performance)
# Also install curl for the HEALTHCHECK
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# IMPORTANT: These must be set BEFORE pip installs llama-cpp-python
# This builds a CPU-only version accelerated with OpenBLAS (much faster inference + more reliable build)
ENV CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS -DLLAMA_NATIVE=OFF" \
    LLAMA_CUBLAS=0 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OPENBLAS_NUM_THREADS=1

# Install Python dependencies (llama-cpp-python will now compile with the flags above)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY main.py .

# Expose port (HF Spaces uses 7860 for Docker Spaces)
EXPOSE 7860

# Healthcheck (HF Spaces shows this in the UI)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Use uvicorn directly (recommended for HF Spaces)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

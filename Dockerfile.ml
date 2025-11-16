# Cyber Sentinel ML - ML Model Service
# Enterprise-grade Docker image with GPU support

FROM nvidia/cuda:11.8-runtime-ubuntu22.04 as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    CUDA_VISIBLE_DEVICES=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for python
RUN ln -s /usr/bin/python3 /usr/bin/python

# Create non-root user
RUN groupadd -r cyber && useradd -r -g cyber cyber

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# Install ML-specific packages
RUN python -m pip install --no-cache-dir \
    tensorflow==2.13.0 \
    torch==2.0.1 \
    torchvision==0.15.2 \
    scikit-learn==1.3.0 \
    pandas==2.0.3 \
    numpy==1.24.3 \
    joblib==1.3.2

# Copy application code
COPY services/ml_service/ ./services/ml_service/
COPY cyber_sentinel_mod.py .
COPY config.py .

# Create necessary directories
RUN mkdir -p logs data models

# Download pre-trained models (placeholder)
RUN echo "Downloading ML models..." && \
    mkdir -p models/threat_detection_v2 && \
    echo "Model placeholder" > models/threat_detection_v2/model.h5

# Set ownership
RUN chown -R cyber:cyber /app

# Switch to non-root user
USER cyber

# Expose port
EXPOSE 9999

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:9999/health || exit 1

# Default command
CMD ["python", "services/ml_service/main.py"]

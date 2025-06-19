# Use Python 3.10.12 as base image
FROM python:3.10.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    DEPLOYMENT_MODE=local \
    HF_SPACES_MODE=1

# Create user for HF Spaces compatibility
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Update package list and install system dependencies from packages.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    unzip \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcb-dri3-0 \
    libgconf-2-4 \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY --chown=user requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY --chown=user . /app

# Ensure user has full read/write permissions on /app directory
RUN chown -R user:user /app && \
    chmod -R 755 /app && \
    mkdir -p /app/cache /app/downloads /app/transcripts && \
    chmod -R 777 /app/cache /app/downloads /app/transcripts

# Switch to user
USER user

# Set user environment
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/app

# Create cache directory
RUN mkdir -p /home/user/.cache

# Expose port
EXPOSE 7860

# Start the application
CMD ["python", "app.py"] 
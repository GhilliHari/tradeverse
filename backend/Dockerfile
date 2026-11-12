# Use official Python 3.10 slim base image for 24/7 Cloud Run / Compute Engine VM
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    TZ=Asia/Kolkata \
    OFFLINE_AUTONOMOUS_MODE=true

WORKDIR /app

# Install system build dependencies and timezone data for NSE market hours (IST)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgomp1 \
    git \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies file
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose backend port 8000
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD curl -f http://localhost:${PORT:-8000}/api/ping || exit 1

# Launch FastAPI backend app (main.py binds to $PORT or 8000)
CMD ["python", "main.py"]

# Use official Python 3.10 slim base image for 24/7 Cloud Run / Compute Engine VM
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1     PYTHONDONTWRITEBYTECODE=1     PORT=8000

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     curl     libgomp1     git     && rm -rf /var/lib/apt/lists/*

# Copy python dependencies file
COPY requirements.txt .

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Expose backend port 8000
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3     CMD curl -f http://localhost:8000/api/terminal/telemetry || exit 1

# Launch FastAPI backend app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

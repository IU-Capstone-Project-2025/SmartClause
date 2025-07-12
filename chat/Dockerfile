FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set executable permissions for scripts
RUN chmod +x scripts/init_db.sh
RUN chmod +x start.sh

# Expose the port
EXPOSE 8002

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the startup script using bash directly
CMD ["bash", "/app/start.sh"] 
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including WeasyPrint requirements
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libfontconfig1-dev \
    libcairo2-dev \
    libgdk-pixbuf2.0-dev \
    libglib2.0-0 \
    libglib2.0-dev \
    libgirepository-1.0-1 \
    gir1.2-glib-2.0 \
    gir1.2-pango-1.0 \
    shared-mime-info \
    && ln -s /usr/lib/$(uname -m)-linux-gnu/libgobject-2.0.so.0 /usr/lib/$(uname -m)-linux-gnu/libgobject-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install the embedding model
COPY scripts/init_model.py .
RUN python init_model.py

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"] 
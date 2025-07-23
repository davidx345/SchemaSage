FROM python:3.11-slim

# Create non-root user
RUN groupadd -r schemauser && useradd -r -g schemauser schemauser

WORKDIR /app

# Set PYTHONPATH to /app for import compatibility
ENV PYTHONPATH=/app

# Install system dependencies required by pdfkit
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory and change ownership to non-root user
RUN mkdir -p /app/uploads && chown -R schemauser:schemauser /app

# Switch to non-root user
USER schemauser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8001/health')" || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

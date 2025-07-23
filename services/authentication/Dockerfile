FROM python:3.11-slim

# Create non-root user
RUN groupadd -r authuser && useradd -r -g authuser authuser

WORKDIR /app

# Install dependencies as root
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R authuser:authuser /app

# Switch to non-root user
USER authuser

# Expose port
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8005/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]

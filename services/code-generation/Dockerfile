FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH to /app for import compatibility
ENV PYTHONPATH=/app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Run the application
CMD ["python", "main.py"]

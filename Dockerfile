# Use official Python runtime as base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements first (optimization for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Set environment variables
ENV PORT=8080

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
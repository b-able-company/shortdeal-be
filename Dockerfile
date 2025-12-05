FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create media directory for Railway Volume mount
RUN mkdir -p /app/media && chmod 755 /app/media

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

EXPOSE 8000

# Use entrypoint script to run migrations and start server
CMD ["./entrypoint.sh"]

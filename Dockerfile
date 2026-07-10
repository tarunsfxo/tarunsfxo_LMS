FROM python:3.11-slim

# Install system dependencies, compilers and runtimes for code execution
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    default-jdk \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# The start command
CMD ["gunicorn", "wsgi:app"]

FROM python:3.11-slim

# ── System-level compiler toolchain ──────────────────────────────────────────
# Install all compilers/runtimes needed by execute_local in blueprints/coding.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build tools
    gcc \
    g++ \
    make \
    # Java (OpenJDK 17 LTS — includes both javac and java)
    default-jdk \
    # Node.js (Debian apt package — LTS version)
    nodejs \
    npm \
    # Ruby interpreter
    ruby \
    # PHP CLI interpreter
    php-cli \
    # Bash (usually pre-installed but explicit for safety)
    bash \
    # General utilities
    curl \
    && rm -rf /var/lib/apt/lists/*

# Make sure java, javac, node, npm are on PATH for gunicorn child processes
ENV PATH="/usr/bin:/usr/local/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

WORKDIR /app

# Copy and install python requirements first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (Render sets $PORT; gunicorn binds to it via wsgi.py)
EXPOSE 10000

# Start command — gunicorn reads PORT env var via wsgi.py
CMD ["gunicorn", "wsgi:app"]


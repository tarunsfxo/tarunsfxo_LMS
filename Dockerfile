FROM python:3.11-slim

# ── System compiler toolchain ─────────────────────────────────────────────────
# Everything needed by execute_local in blueprints/coding.py
RUN apt-get update && apt-get install -y --no-install-recommends \
    # C / C++ compilers
    gcc \
    g++ \
    make \
    # Java (OpenJDK — includes javac + java + jar)
    default-jdk \
    # Node.js + npm (JavaScript)
    nodejs \
    npm \
    # Ruby
    ruby \
    # PHP CLI
    php-cli \
    # Shell / utilities
    bash \
    curl \
    # Locate / find helpers for debugging
    findutils \
    && rm -rf /var/lib/apt/lists/*

# ── Set JAVA_HOME dynamically (works regardless of JDK version / arch) ────────
# We find the real javac binary and derive JAVA_HOME from it.
RUN JAVAC_PATH=$(readlink -f $(which javac)) \
    && JAVA_HOME=$(dirname $(dirname $JAVAC_PATH)) \
    && echo "JAVA_HOME=$JAVA_HOME" >> /etc/environment \
    && echo "export JAVA_HOME=$JAVA_HOME" >> /etc/profile.d/java.sh \
    && echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/profile.d/java.sh

# Expose JAVA_HOME as a proper Docker ENV (so gunicorn child processes see it)
RUN JAVAC_PATH=$(readlink -f $(which javac)) \
    && echo "$(dirname $(dirname $JAVAC_PATH))" > /tmp/java_home
ENV JAVA_HOME=/usr/lib/jvm/default-java

# ── Prepend JAVA_HOME/bin + system bins to PATH ───────────────────────────────
ENV PATH="${JAVA_HOME}/bin:/usr/bin:/usr/local/bin:/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# ── Verify all compilers are working (build fails if any are missing) ─────────
RUN python3 --version \
    && gcc --version \
    && g++ --version \
    && javac --version \
    && java --version \
    && node --version \
    && npm --version \
    && ruby --version \
    && php --version | head -1 \
    && echo "✅ All compilers verified"

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Render injects $PORT; gunicorn reads it via wsgi.py)
EXPOSE 10000

# Start gunicorn
CMD ["gunicorn", "wsgi:app"]

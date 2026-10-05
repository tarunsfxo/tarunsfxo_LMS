FROM python:3.11-slim

# ── System compiler toolchain ─────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    # Java — default-jdk-headless is lighter and more reliable on slim images
    default-jdk-headless \
    # Node.js + npm
    nodejs \
    npm \
    # Ruby
    ruby \
    # PHP CLI
    php-cli \
    bash \
    curl \
    findutils \
    && rm -rf /var/lib/apt/lists/*

# ── Bake the exact javac / java paths into /etc so Python can read them ───────
# This is the most reliable approach: at build time, when javac is definitely
# installed, we resolve its real absolute path and write it to a file.
# Python reads /etc/javac_path and /etc/java_path at startup — no PATH needed.
RUN set -e; \
    JAVAC=$(find /usr -name javac -type f 2>/dev/null | head -1); \
    JAVA=$(find /usr -name java  -type f 2>/dev/null | head -1); \
    echo "Found javac: $JAVAC"; \
    echo "Found java:  $JAVA"; \
    echo "$JAVAC" > /etc/javac_path; \
    echo "$JAVA"  > /etc/java_path; \
    JAVA_HOME=$(dirname $(dirname $JAVAC)); \
    echo "JAVA_HOME: $JAVA_HOME"; \
    echo "export JAVA_HOME=$JAVA_HOME" >> /etc/profile; \
    echo "export PATH=$JAVA_HOME/bin:\$PATH" >> /etc/profile

# ── Docker ENV so gunicorn child processes inherit JAVA_HOME / PATH ───────────
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:/usr/bin:/usr/local/bin:/bin:/usr/sbin:/sbin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# ── Build-time smoke test: fail the build if any compiler is missing ──────────
RUN echo "=== Compiler Verification ===" \
    && python3   --version \
    && gcc       --version | head -1 \
    && g++       --version | head -1 \
    && cat /etc/javac_path && $(cat /etc/javac_path) --version \
    && cat /etc/java_path  && $(cat /etc/java_path)  --version \
    && node      --version \
    && npm       --version \
    && ruby      --version \
    && php       --version | head -1 \
    && echo "=== All compilers OK ==="

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "wsgi:app"]

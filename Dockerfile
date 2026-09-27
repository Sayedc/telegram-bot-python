FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PATH="/usr/bin:${PATH}"
ENV YTDLP_JS_RUNTIMES=node

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    wget \
    ca-certificates \
    xvfb \
    xauth \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    && npm install -g bun \
    && node --version \
    && npm --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir -U "yt-dlp[default]"

RUN playwright install chromium
RUN playwright install-deps chromium || true

COPY . .

RUN mkdir -p /app/downloads

# ✅ التشغيل العادي
CMD ["python", "main.py"]

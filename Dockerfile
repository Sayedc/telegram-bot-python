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
    nodejs \
    npm \
    && npm install -g bun \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir -U "yt-dlp[default]"

COPY . .

RUN mkdir -p /app/downloads

CMD ["python", "main.py"]

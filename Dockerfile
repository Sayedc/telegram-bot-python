FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
ffmpeg \
git \
nodejs \
npm \
curl \
wget \
ca-certificates \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -U yt-dlp

COPY . .

ENV YTDLP_JS_RUNTIMES=node
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]

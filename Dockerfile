FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

COPY . .

RUN pip install --no-cache-dir python-telegram-bot yt-dlp

CMD ["python", "main.py"]

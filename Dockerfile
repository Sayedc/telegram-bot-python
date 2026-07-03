FROM python:3.10-slim

# تثبيت الأدوات المطلوبة
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تثبيت أحدث نسخة Nightly من yt-dlp
RUN pip uninstall -y yt-dlp || true
RUN pip install --pre -U yt-dlp

COPY . .

CMD ["python", "main.py"]

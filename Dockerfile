FROM python:3.10-slim

# تثبيت FFmpeg و Git
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملف المتطلبات أولاً (لتسريع عملية البناء)
COPY requirements.txt .

# تحديث pip وتثبيت المتطلبات
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]

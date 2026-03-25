FROM python:3.12-slim

WORKDIR /app

# تثبيت ffmpeg (مهم عشان mp3 يشتغل)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# نسخ المتطلبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي الملفات
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]

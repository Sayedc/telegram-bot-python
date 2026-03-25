FROM python:3.10

WORKDIR /app

COPY . .

RUN apt update && apt install -y ffmpeg

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml .

RUN uv sync --no-dev

COPY . .

CMD ["python", "main.py"]

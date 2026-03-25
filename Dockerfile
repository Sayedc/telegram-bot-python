FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml .

RUN uv sync --no-dev

COPY . .

CMD ["python", "main.py"]

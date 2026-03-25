FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir --upgrade pip uv

# Copy only pyproject
COPY pyproject.toml .

# Install dependencies
RUN uv sync --no-dev

# Copy

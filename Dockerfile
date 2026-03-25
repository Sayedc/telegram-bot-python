FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir --upgrade pip uv

# Copy only pyproject (no uv.lock)
COPY pyproject.toml

# Install dependencies
RUN uv sync --no-dev

# Copy project files
COPY . .

# Run the bot
CMD ["python", "main.py"]

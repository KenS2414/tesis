FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Build deps for compiling wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev libjpeg-dev zlib1g-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a self-contained prefix
COPY requirements.txt ./
# Ensure gunicorn is available at runtime even if not present in requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt gunicorn

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Runtime system libraries required by some wheels (keep minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN addgroup --system app && adduser --system --group app

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . /app

RUN chown -R app:app /app
USER app

ENV FLASK_APP=app:create_app
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]

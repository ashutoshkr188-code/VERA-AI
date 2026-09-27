FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV PORT=8080
ENV LLM_PROVIDER=hosted
ENV HOSTED_LLM_URL=https://api.openai.com/v1/chat/completions
ENV HOSTED_LLM_MODEL=gpt-4o-mini
ENV DATABASE_URL=sqlite:///./vera.db

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/v1/healthz || exit 1

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
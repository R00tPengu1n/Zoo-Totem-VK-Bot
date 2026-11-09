FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY data ./data

# Бот работает не от root — так безопаснее
RUN useradd --create-home botuser \
    && mkdir -p storage logs \
    && chown -R botuser:botuser /app
USER botuser

CMD ["python", "-m", "bot"]

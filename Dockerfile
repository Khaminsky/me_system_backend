FROM python:3.13-alpine

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apk add --no-cache \
    postgresql-client \
    netcat-openbsd \
    gcc \
    && rm -rf /var/cache/apk/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && rm requirements.txt

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh 2>/dev/null || sed -i 's/\r$//' /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

RUN mkdir -p /app/uploads /app/cleaned_uploads

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "core.wsgi:application"]

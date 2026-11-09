# FULL scanner app (dashboard + poller) — Render/any Docker host
FROM python:3.14-slim

WORKDIR /app

RUN pip install --no-cache-dir "curl_cffi>=0.11"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0

COPY config.py run.py /app/
COPY scanner/ /app/scanner/
COPY data/mis_allowed.json /app/data/mis_allowed.json

EXPOSE 8787

CMD ["python", "-u", "run.py"]

# NSE pre-open scanner — cloud probe image (ClawCloud Run)
FROM python:3.14-slim

WORKDIR /app

# sirf wahi dependency jo theek kaam karti he (nse_client ka curl_cffi)
RUN pip install --no-cache-dir "curl_cffi>=0.11"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# nse_client ko import karne ke liye scanner package
COPY scanner/__init__.py scanner/nse_client.py /app/scanner/
COPY deploy/probe.py /app/probe.py

EXPOSE 8787

CMD ["python", "-u", "probe.py"]

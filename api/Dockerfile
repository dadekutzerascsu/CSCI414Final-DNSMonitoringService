FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dns_lookup.py main.py import_domains.py run-api.sh ./
RUN chmod +x /app/run-api.sh

EXPOSE 8000
CMD ["/bin/sh", "/app/run-api.sh"]

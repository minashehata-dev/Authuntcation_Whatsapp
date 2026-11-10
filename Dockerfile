# Written by blitz.cloud for this project. It is yours now: blitz.cloud
# builds from it as it is, and you can change it like any other file.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend (Python) dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install gateway (Node) dependencies
COPY whatsapp_gateway/package.json whatsapp_gateway/package-lock.json whatsapp_gateway/
WORKDIR /app/whatsapp_gateway
RUN npm ci --omit=dev
WORKDIR /app

# Copy application source, keeping original layout
COPY backend backend
COPY whatsapp_gateway whatsapp_gateway

# Ensure Baileys session storage is writable by the non-root user
RUN mkdir -p /app/whatsapp_gateway/sessions/baileys_auth \
    && chown -R 1000:1000 /app/whatsapp_gateway/sessions

ENV PORT=8080
EXPOSE 8080

USER 1000:1000

# The Node gateway is only used internally by the backend, so give it a
# separate fixed internal port (not the public PORT) to avoid clashing
# with uvicorn, which binds the public PORT.
CMD ["sh", "-c", "cd /app/whatsapp_gateway && PORT=3001 node src/index.js & cd /app/backend && exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

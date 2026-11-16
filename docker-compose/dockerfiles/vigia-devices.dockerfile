# Worker mock vigia-devices — context = monorepo root
FROM python:3.12-slim AS final

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY vigia-devices/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vigia-devices/main.py .
COPY vigia-devices/device_pool.json .
COPY vigia-devices/worker/ ./worker/
# Vídeos mock embutidos na imagem (obrigatórios em runtime).
COPY vigia-devices/assets/videos/ ./assets/videos/

RUN set -eu; \
    count="$(find ./assets/videos -type f \
      \( -iname '*.mp4' -o -iname '*.avi' -o -iname '*.mkv' -o -iname '*.mov' \) \
      | wc -l)"; \
    test "${count}" -ge 1

ENV ASSETS_DIR=/app/assets/videos \
    DEVICE_POOL_PATH=/app/device_pool.json \
    PYTHONUNBUFFERED=1

CMD ["python", "-u", "main.py"]

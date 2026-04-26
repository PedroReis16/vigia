FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app/fall-detection

# Avoid .pyc files and force unbuffered logs in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Copy only dependency manifest first to maximize Docker layer cache.
COPY fall-detection/requirements.txt ./requirements.txt

# Install dependencies (pin pip version to satisfy DL3013)
RUN python -m pip install --no-cache-dir "pip==26.0.1" && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy only fall-detection service files (avoid shipping whole monorepo).
COPY fall-detection/ ./

# Expose the port the app runs on
EXPOSE 8000

# main.py adiciona src/ ao path; alternativa: PYTHONPATH=src python -m app
CMD ["python", "main.py"]
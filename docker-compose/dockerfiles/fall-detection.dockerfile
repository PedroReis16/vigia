FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app/fall-detection

# Avoid .pyc files and force unbuffered logs in containers.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# Manifests: headless OpenCV (sem libGL no container).
COPY fall-detection/requirements-common.txt fall-detection/requirements-headless.txt ./

# Install dependencies (pin pip version to satisfy DL3013).
# ultralytics puxa opencv-python; remover e fixar headless (sem libGL no container).
RUN python -m pip install --no-cache-dir "pip==26.0.1" && \
    python -m pip install --no-cache-dir -r requirements-headless.txt && \
    python -m pip uninstall -y opencv-python 2>/dev/null || true && \
    python -m pip install --no-cache-dir --force-reinstall "opencv-python-headless==4.12.0.88"

# Copy only fall-detection service files (avoid shipping whole monorepo).
COPY fall-detection/ ./

# Expose the port the app runs on
EXPOSE 8000

# main.py adiciona src/ ao path; alternativa: PYTHONPATH=src python -m app
CMD ["python", "main.py"]
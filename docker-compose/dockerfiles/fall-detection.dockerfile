FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY fall-detection/requirements.txt ./

# Install dependencies (pin pip version to satisfy DL3013)
RUN python -m pip install --no-cache-dir "pip==26.0.1" && \
    python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

WORKDIR /app/fall-detection

# Expose the port the app runs on
EXPOSE 8000

# main.py adiciona src/ ao path; alternativa: PYTHONPATH=src python -m app
CMD ["python", "main.py"]
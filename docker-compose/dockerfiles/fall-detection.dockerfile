FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY fall-detection/requirements.txt ./

# Install dependencies (upgrade pip first; setuptools>=82 removes vendored jaraco.context 5.3.0 flagged by Trivy)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

WORKDIR /app/fall-detection

# Expose the port the app runs on
EXPOSE 8000

# main.py adiciona src/ ao path; alternativa: PYTHONPATH=src python -m app
CMD ["python", "main.py"]
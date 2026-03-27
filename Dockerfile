FROM python:3.11-slim

# Install mpg123 and ALSA for audio output
RUN apt-get update && apt-get install -y --no-install-recommends \
    mpg123 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

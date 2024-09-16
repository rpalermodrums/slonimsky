FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    fluidsynth \
    alsa-utils \
    libasound2-dev \
    pulseaudio \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN pulseaudio --start --daemonize
CMD ["python", "slonimsky.py"]

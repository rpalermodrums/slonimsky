FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y fluidsynth

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "slonimsky.py"]

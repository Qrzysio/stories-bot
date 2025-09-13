FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

WORKDIR /app
COPY requirements.txt ./
RUN  pip install --no-cache-dir -r requirements.txt
COPY . .

RUN apt-get update && apt-get install -y ffmpeg
RUN mkdir -p /data/cookies

CMD ["python", "api.py"]
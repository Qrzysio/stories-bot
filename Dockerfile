FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

WORKDIR /app
COPY requirements.txt ./
RUN  pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /data/uploads /data/cookies

CMD ["python", "stories_bot_server.py"]
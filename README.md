# bot-relacje-facebook-playwrite

Post story:

curl -X POST http://srv10.mikr.us:20149/post_story -H "Content-Type: application/json" -d '{
    "service_id": "57578687868767",
    "image_path": "https://www.exampl.pl/grafika/fb_posty/relacje/2025/07/30/688a1cfd4875f.jpg",
    "link": "https://www.example.pl/art/1753881856/ostroleka-pamieta-uroczystosci-miejskie-juz-w-piatek-1-sierpnia-2025-r",
    "hash": "1234567890009876",
    "headless": true,
    "format": "film"             # "image" | "film" - not necessarily
}'


Send cookies:

curl -X POST http://srv10.mikr.us:20149/upload_cookies -H "Content-Type: application/json" -d '{
    "service_id": "57578687868767",
    "cookies": cookies
}'


Get all data from db:

curl -X POST http://srv10.mikr.us:20149/get_db_data -H "Content-Type: application/json" -d '{
    "hash": "1234567890009876",
}'







For developer:


create images
send images
send config.yaml
send stories.db
delete "build" from composer and change image name
send docker-compose
create /data/cookies/
mv config.yaml and stories.db to /data/
unpack images
composer up
load cookies for accounts




old compose:



services:
  fb_story_bot:
#    build: .                 #del on server
    image: mybot:latest
    container_name: fb_story_bot
    ports:
      - "20149:5000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
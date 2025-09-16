# bot-relacje-facebook-playwrite


Post story:

curl -X POST http://srv10.mikr.us:20149/post_story -H "Content-Type: application/json" -d '{
    "service_id": "57578687868767",
    "image_url": "https://www.exampl.pl/grafika/fb_posty/relacje/2025/07/30/688a1cfd4875f.jpg",
    "link": "https://www.example.pl/art/1753881856/ostroleka-pamieta-uroczystosci-miejskie-juz-w-piatek-1-sierpnia-2025-r",
    "hash": "1234567890009876",
    "headless": false,          # not necessarily
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
image to .tar (sudo docker save -o fb_story_api.tar bot-relacje-facebook-playwrite_fb_story_api:latest)
send images (sudo scp -P 10149 fb_story_api.tar root@halina149.mikrus.xyz:/root/)
tar to image on server (docker load -i fb_story_api.tar)
send config.yaml
send stories.db
delete "build" from composer and change image name
send docker-compose
create /data/cookies/
mv config.yaml and stories.db to /data/
composer up
load cookies for accounts


ssh -p 10149 -L 6080:localhost:6080 root@halina149.mikrus.xyz - connect to container by ssh
http://localhost:6080/vnc.html - see container browser
#______________________________________________________________________________________________________
# Zainstaluj python, requests, json, chrome (bot dziala w dockerze z chromem)
#
# W Chrome zainstaluj rozszerzenie "EditThisCookie V3"
#
# Zaloguj się na Facebooku
#
# Wejdź w rozszerzenie "EditThisCookie V3" i kliknij u góry "Export"
#
# Wklej dane cookie do pliku "cookie.json" w tym folderze (zastąp stare dane nowymi)
#______________________________________________________________________________________________________
# Skopiuj obraz do 'client' folderu i zmień jego nazwę na "image.jpg"
#
# Wypełnij te pola:

SERVICE_ID = "7137490626"

LINK = "https://www.moja-ostroleka.pl"

FILE_URL = "https://www.moja-ostroleka.pl/grafika/fb_posty/relacje/2025/07/30/688a1cfd4875f.jpg"

HASH = "110a6224756c872b733f7e99d72f9f1ae33bb11"

# Uruchom client.py
#______________________________________________________________________________________________________


from send_cookies_api import send_cookies_api
from send_story_api import send_story_api
COOKIES_FILE_NAME = "cookie.json"
FILE_NAME = "image.jpg"

#______________________________________________ comment on unnecessary ________________________________
def main(service_id):
    send_cookies_api(cookies_path=COOKIES_FILE_NAME, service_id=service_id)
    # send_story_api(service_id=service_id, image_path=FILE_URL, link=LINK, hash_data=HASH)
#______________________________________________________________________________________________________



if __name__ == "__main__":
    main(service_id=SERVICE_ID)

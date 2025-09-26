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

SERVICE_ID = "102525192808192"

LINK = "https://www.moja-ostroleka.pl/art/1758707501/policja-lapala-pijanych-na-ulicach-wczorajsi-kierowcy-a-jeden-z-ponad-2-promilami"

FILE_URL = "https://www.moja-ostroleka.pl/grafika/fb_posty/relacje/2025/09/24/68d44f4adce14.jpg"

HASH = "e0f8b35e6d329fe21cd95b72f465d28183fc1c7b97ef66d055fcdbdc8df62011"

# Uruchom client.py
#______________________________________________________________________________________________________


from send_cookies_api import send_cookies_api
from send_story_api import send_story_api
from get_db_data import get_db_data
COOKIES_FILE_NAME = "cookie.json"

#______________________________________________ comment on unnecessary ________________________________
def main(service_id):
    # send_cookies_api(cookies_path=COOKIES_FILE_NAME, service_id=service_id)
    send_story_api(service_id=service_id, image_path=FILE_URL, link=LINK, hash_data=HASH)
    # get_db_data(hash_data=HASH)
#______________________________________________________________________________________________________



if __name__ == "__main__":
    main(service_id=SERVICE_ID)

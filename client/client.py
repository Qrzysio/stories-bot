#______________________________________________________________________________________________________
# Zainstaluj python, requests, json, chrome
#
# W Chrome zainstaluj rozszerzenie "EditThisCookie V3"
#
# Zaloguj się na Facebooku
#
# Wejdź w rozszerzenie "EditThisCookie V3" i kliknij u góry "Export"
#
# Wklej dane cookie do pliku cookie.json w tym folderze (zastąp stare dane nowymi)
#______________________________________________________________________________________________________
# Skopiuj obraz do tego folderu i zmień jego nazwę na image.jpg
#
# Wypełnij te pola:
#
SERVICE_ID_LIST = ["193617547354036",]
#
LINK = "example.com"
#
# Uruchom client.py
#______________________________________________________________________________________________________



from send_cookies_api import send_cookies_api
from send_file_api import send_file_api
from send_story_api import send_story_api


COOKIES_FILE_NAME = "cookie.json"
FILE_NAME = "image.jpg"


def main(service_id):
    send_cookies_api(cookies_path=COOKIES_FILE_NAME, service_id=service_id)
    send_file_api(image_path=FILE_NAME)
    send_story_api(service_id=service_id, image_path=FILE_NAME, link=LINK)


if __name__ == "__main__":
    for service_id in SERVICE_ID_LIST:
        main(service_id)

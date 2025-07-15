# Установи python, requests, json, chrome

# В Chrome установи расширение "EditThisCookie V3"

# Зайди на фб и залогинся

# Зайди в расширение "EditThisCookie V3" и нажми сверху "Export"

# Вставь данные cookie в файл cookie.json в этой папке (старые данные замени на новые)

# Cкопируй изображение в эту же папку и переименуй его на image.jpg

# Заполни эти поля:
SERVICE_ID_LIST = ["193617547354036", "713714068490626"]
LINK = "example.com"

# Выполни client.py




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

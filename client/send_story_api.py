import requests


def send_story_api(service_id, image_path, link, hash_data):
    url = "http://localhost:20149/post_story"

    payload = {
        "service_id": service_id,
        # "image_path": image_path,   #for old bot
        "image_url": image_path,
        "link": link,
        "hash": hash_data,
        "headless": False,            #not necessarily
        "format": "film"            #not necessarily
    }

    response = requests.post(url, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())

import requests


def send_story_api(service_id, image_path, link, hash_data):
    url = "http://stories.editio.app/post_story"

    payload = {
        "service_id": service_id,
        "image_url": image_path,
        "link": link,
        "hash": hash_data,
        "headless": False,            #not necessarily
        # "format": "video"            #not necessarily
    }

    response = requests.post(url, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())

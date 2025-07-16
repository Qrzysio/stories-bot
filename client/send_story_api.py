import requests
# from client.client import SERVICE_ID, FILE_NAME, LINK


def send_story_api(service_id, image_path, link):
    url = "http://srv10.mikr.us:20149/post_story"

    payload = {
        "service_id": service_id,
        "image_path": image_path,
        "link": link,
        "headless": True
    }

    response = requests.post(url, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())



# if __name__ == "__main__":
#     send_story_api(SERVICE_ID, FILE_NAME, LINK)
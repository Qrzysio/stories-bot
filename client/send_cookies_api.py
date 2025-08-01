import json
import requests


def send_cookies_api(cookies_path, service_id):
    url = "http://srv10.mikr.us:20149/upload_cookies"
    # Download cookie from file
    with open(cookies_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    # Made payload
    payload = {
        "service_id": service_id,
        "cookies": cookies
    }

    # Send POST-request
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload
    )

    # Result
    print(f"Status: {response.status_code}")
    print("Response:", response.json())


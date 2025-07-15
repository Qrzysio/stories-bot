import json
import requests
# from client.client import COOKIES_FILE_NAME, SERVICE_ID


def send_cookies_api(cookies_path, service_id):

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
        "http://localhost:5000/upload_cookies",
        headers={"Content-Type": "application/json"},
        json=payload
    )

    # Result
    print(f"Status: {response.status_code}")
    print("Response:", response.json())


# if __name__ == "__main__":
#     send_cookies_api(COOKIES_FILE_NAME, SERVICE_ID)

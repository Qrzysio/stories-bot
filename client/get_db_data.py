import requests


def get_db_data(hash_data):
    url = "http://srv10.mikr.us:30149/get_db_data"

    payload = {
        "hash": hash_data,
    }

    response = requests.post(url, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())
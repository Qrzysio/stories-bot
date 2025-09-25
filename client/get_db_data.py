import requests


def get_db_data(hash_data):
    url = "http://localhost:5000/get_db_data"

    payload = {
        "hash": hash_data,
    }

    response = requests.post(url, json=payload)

    print("Status:", response.status_code)
    print("Response:", response.json())
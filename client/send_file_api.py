import requests
# from client.client import FILE_NAME


def send_file_api(image_path):
    url = "http://srv10.mikr.us:20149/upload_image"

    with open(image_path, "rb") as f:
        files = {'file': (image_path, f)}
        response = requests.post(url, files=files)

    print(response.status_code)
    print(response.json())


# if __name__ == "__main__":
#     send_file_api(FILE_NAME)
import os
from pathlib import Path

from flask import Flask, request, jsonify
from playwright_bot_stories import post_story, save_cookies_json


UPLOADS_DIR = Path("/data/uploads")

app = Flask(__name__)

@app.route('/post_story', methods=['POST'])
def handler():
    data = request.get_json()
    image_path = data.get("image_path")
    link = data.get("link")
    service_id = data.get("service_id")
    headless = data.get("headless")

    print(f"[API] REQUEST FOR POST STORY: image={image_path}, link={link}, id={service_id}")
    try:
        post_story(
            service_id=service_id,
            image_path=image_path,
            link=link,
            headless=headless
        )
        return jsonify({"status": "success", "message": f"Story for {service_id} posted successfully."})
    except Exception as e:
        print(f"[ERROR] REQUEST FOR POST - NEGATIVE: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/upload_cookies', methods=['POST'])
def upload_cookies():
    data = request.get_json()
    service_id = data.get('service_id')
    cookies = data.get('cookies')

    print(f"[API] REQUEST FOR UPLOAD COOKIES")

    if not service_id or not cookies:
        print("[ERROR] Should send 'service_id' and 'cookies'")
        return jsonify({"status": "error", "error": "Should send 'service_id' and 'cookies'"}), 400

    try:
        save_cookies_json(service_id, cookies)
        print("[SUCCESS] COOKIES UPLOAD - COMPLETE")
        return jsonify({"status": "success", "message": f"Cookies for {service_id} saved."})
    except Exception as e:
        print(f"[ERROR] COOKIES UPLOAD - NEGATIVE: {e}")
        return jsonify({"status": "error", "error": "Cookeis doesn't save"}), 500


@app.route("/upload_image", methods=["POST"])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    filename = file.filename
    if filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        save_path = UPLOADS_DIR / filename
        file.save(save_path)
        return jsonify({"status": "success", "message": f"{filename} uploaded successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
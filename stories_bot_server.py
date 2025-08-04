import os
from flask import Flask, request, jsonify
from playwright_bot_stories import (
    post_story,
    save_cookies_json,
    load_config,
    is_url_valid, validate_image_from_url, download_image,
)


app = Flask(__name__)
fb_profiles = load_config()


@app.route('/post_story', methods=['POST'])
def handler():
    data = request.get_json()
    image_path = data.get("image_path")
    link = data.get("link")
    service_id = data.get("service_id")
    headless = data.get("headless")
    client_hash = data.get("hash")

    # Check image_path exist
    if not image_path:
        return jsonify({"status": "error", "error": "image_path is required"}), 400

    # Check link exist
    if not link:
        return jsonify({"status": "error", "error": "link is required"}), 400

    # Check service_id exist
    if not service_id:
        return jsonify({"status": "error", "error": "service_id is required"}), 400

    # Check headless exist
    if not headless:
        return jsonify({"status": "error", "error": "headless is required"}), 400

    # Check client_hash exist
    if not client_hash:
        return jsonify({"status": "error", "message": "client_hash is required"}), 400

    print(f"[API] REQUEST FOR POST STORY: image={image_path}, link={link}, id={service_id}")

    # Checking service_id in config
    if service_id not in fb_profiles:
        return jsonify({"status": "error", "message": f"Service ID {service_id} not found in config file"}), 400

    # Check if this service_id has a hash in the config
    server_hash = fb_profiles[service_id].get("hash")
    if not server_hash:
        return jsonify({"status": "error", "error": f"No hash defined for service_id in config file'{service_id}'"}), 400

    # Comparing hashes
    if client_hash != server_hash:
        return jsonify({"status": "error", "error": "Hash mismatch"}), 400

    # Image verification
    image_bytes, error = validate_image_from_url(image_path)
    if error:
        return jsonify({
            "status": "error",
            "error": f"Image validation failed: {error}"
        }), 400

    # Download image
    image_file, error = download_image(image_bytes)
    if error:
        return jsonify({"status": "error", "error": f"{error}"}), 400

    # Check link
    if not is_url_valid(link):
        return jsonify({"status": "error", "error": "Invalid link URL"}), 400

    try:
        post_story(
            service_id=service_id,
            image_path=image_file,
            link=link,
            headless=headless
        )
        return jsonify({"status": "success", "message": f"Story for {service_id} posted successfully."}), 200
    except Exception as e:
        print(f"[ERROR] REQUEST FOR POST - NEGATIVE: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if image_file and os.path.exists(image_file):
            os.remove(image_file)


@app.route('/upload_cookies', methods=['POST'])
def upload_cookies():
    data = request.get_json()
    service_id = data.get('service_id')
    cookies = data.get('cookies')

    print(f"[API] REQUEST FOR UPLOAD COOKIES")

    if not service_id or not cookies:
        print("[ERROR] Should send 'service_id' and 'cookies'")
        return jsonify({"status": "error", "error": "'Service_id' and 'cookies' required"}), 400

    try:
        save_cookies_json(service_id, cookies)
        print("[SUCCESS] COOKIES UPLOAD - COMPLETE")
        return jsonify({"status": "success", "message": f"Cookies for {service_id} saved."}), 200
    except Exception as e:
        print(f"[ERROR] COOKIES UPLOAD - NEGATIVE: {e}")
        return jsonify({"status": "error", "error": "Cookeis doesn't save"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
import os
from flask import Flask, request, jsonify
from db import SessionLocal, engine
from models import Base, StoryQueue
from playwright_bot_stories import (
    post_story,
    save_cookies_json,
    load_config,
    is_url_valid,
    validate_image_from_url,
    download_image,
)

Base.metadata.create_all(engine)

app = Flask(__name__)
fb_profiles = load_config()

@app.route("/enqueue_story", methods=["POST"])
def enqueue_story():
    data = request.get_json()
    service_id = data.get("service_id")
    image_url = data.get("image_url")
    link = data.get("link")
    headless = data.get("headless")
    client_hash = data.get("hash")

    # Check image_path exist
    if not image_url:
        return jsonify({"status": "error", "error": "image_url is required"}), 400

    # Check link exist
    if not link:
        return jsonify({"status": "error", "error": "link is required"}), 400

    # Check service_id exist
    if not service_id:
        return jsonify({"status": "error", "error": "service_id is required"}), 400

    # # Check headless exist
    # if headless is None:
    #     return jsonify({"status": "error", "error": "headless is required"}), 400

    # Check client_hash exist
    if not client_hash:
        return jsonify({"status": "error", "message": "client_hash is required"}), 400

    print(f"[API] REQUEST FOR ADDING TO QUEUE: image={image_url}, link={link}, id={service_id}")

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
    image_bytes, error = validate_image_from_url(image_url)
    if error:
        return jsonify({
            "status": "error",
            "error": f"Image validation failed: {error}"
        }), 400

    # Check link
    if not is_url_valid(link):
        return jsonify({"status": "error", "error": "Invalid link URL"}), 400

    session = SessionLocal()
    try:
        story = StoryQueue(
            service_id=service_id,
            image_url=image_url,
            link=link,
            status="pending",
            headless=headless,
        )

        session.add(story)
        session.commit()
        return jsonify({"status": "success", "id": story.id}), 200
    finally:
        session.close()



# webhook_url = fb_profiles[service_id].get("webhook_url")

# # Download image
# image_file, error = download_image(image_bytes)
# if error:
#     return jsonify({"status": "error", "error": f"{error}"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

import os
from flask import Flask, request, jsonify
from db import SessionLocal, engine
from models import Base, StoryQueue
from playwright_bot_stories import (
    save_cookies_json,
    load_config,
    is_url_valid,
    validate_image_from_url,
)

Base.metadata.create_all(engine)

app = Flask(__name__)
fb_profiles = load_config()

@app.route("/post_story", methods=["POST"])
def enqueue_story():
    data = request.get_json()
    service_id = data.get("service_id")
    image_url = data.get("image_url")
    link = data.get("link")
    headless = data.get("headless")
    client_hash = data.get("hash")
    format = data.get("format")

    # Check image_path exist
    if not image_url:
        return jsonify({"status": "error", "error": "image_url is required"}), 400

    # Check link exist
    if not link:
        return jsonify({"status": "error", "error": "link is required"}), 400

    # Check service_id exist
    if not service_id:
        return jsonify({"status": "error", "error": "service_id is required"}), 400

    # Check client_hash exist
    if not client_hash:
        return jsonify({"status": "error", "error": "client_hash is required"}), 400

    print(f"[API] REQUEST FOR ADDING TO QUEUE: image={image_url}, link={link}, id={service_id}")

    # Checking service_id in config
    if service_id not in fb_profiles:
        return jsonify({"status": "error", "error": f"Service ID {service_id} not found in config file"}), 400

    # Check if this service_id has a hash in the config
    server_hash = fb_profiles[service_id].get("hash")
    if not server_hash:
        return jsonify({"status": "error", "error": f"No hash defined for service_id in config file'{service_id}'"}), 400

    # Check if format has a valid value
    valid_format =["image", "film"]
    if format:
        if format not in valid_format:
            return jsonify({"status": "error", "error": "format value should be 'image' or 'film'"}), 400

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
            format=format if format else "image"
        )

        session.add(story)
        session.commit()
        return jsonify({
            "status": "success",
            "job_id": story.id,
            "message": "Przyjeto do publikacji",
            "data": story.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }), 202
    finally:
        session.close()


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


@app.route("/get_db_data", methods=["POST"])
def get_db_data():
    data = request.get_json()
    client_hash = data.get("hash")

    if not client_hash:
        return jsonify({"status": "error", "error": "client hash is required"}), 400

    print(f"[API] REQUEST FOR DB DATA")

    if not any(cfg.get("hash") == client_hash for cfg in fb_profiles.values()):
        return jsonify({"status": "error", "error": "Invalid client hash"}), 403

    session = SessionLocal()
    try:
        stories = session.query(StoryQueue).all()
        result = []
        for s in stories:
            result.append({
                "job_id": s.id,
                "service_id": s.service_id,
                "image_url": s.image_url,
                "link": s.link,
                "status": s.status,
                "format": s.format,
                "retries": s.retries,
                "max_retries": s.max_retries,
                "next_attempt": s.next_attempt.strftime("%Y-%m-%d %H:%M:%S") if s.next_attempt else None,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "last_error": s.last_error,
            })

        return jsonify({"status": "success", "stories": result}), 200
    finally:
        session.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

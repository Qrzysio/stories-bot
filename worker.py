import random
import time

import requests
from flask import jsonify
from datetime import datetime, timedelta, timezone
from db import SessionLocal, engine
from models import Base, StoryQueue
from playwright_bot_stories import (
    post_story,
    download_image,
    validate_image_from_url,
    load_config,
    convert_to_mp4
)


CHECK_INTERVAL = random.randint(7, 22)          # sec
MIN_DELAY = 1                                       # min
MAX_DELAY = 2                                      # min

Base.metadata.create_all(engine)
fb_profiles = load_config()


def generate_delays_linear(max_retries, min_delay, max_delay):
    if max_retries <= 1:
        return [min_delay]
    step = (max_delay - min_delay) / (max_retries - 1)
    return [min(round(min_delay + i * step), max_delay) for i in range(max_retries)]


def calculate_next_attempt(retries, max_retries):
    delays = generate_delays_linear(max_retries, MIN_DELAY, MAX_DELAY)
    if retries < max_retries:
        return datetime.now() + timedelta(minutes=delays[retries-1])
    else:
        return None


def process_story(story, session):
    try:
        print(f"[WORKER] (job_id:{story.id}) Processing story for {story.service_id}")
        story.story_status = "in_progress"
        story.updated_at = datetime.now()
        session.commit()


        # Image verification again
        image_bytes, error = validate_image_from_url(story.image_url)
        if error:
            return jsonify({
                "status": "error",
                "error": f"Image again validation failed: {error}"
            }), 400

        # Download image
        image_file, error = download_image(image_bytes)
        if error:
            return jsonify({"status": "error", "error": f"{error}"}), 400

        # Convert to mp4
        if story.format == "video":
            converted_file, error = convert_to_mp4(image_file)
            if error:
                story.story_status = "failed"
                story.updated_at = datetime.now()
                story.last_error = f"FFMPEG error: {error}"
                story.next_attempt = None
                session.commit()
                print(f"[WORKER] Story {story.id} failed at ffmpeg: {error}")
                return jsonify({"status": "error", "error": f"{error}"}), 400
            media_file = converted_file
            print(f"[WORKER] Media file converted via ffmpeg to .mp4")
            instagram = fb_profiles[story.service_id].get("has_instagram")
            if instagram is True:
                num_tabs = 13   # -1 if start locally without docker
            else:
                num_tabs = 11   # -1 if start locally without docker
        else:
            media_file = image_file
            instagram = fb_profiles[story.service_id].get("has_instagram")
            if instagram is True:
                num_tabs = 8
            else:
                num_tabs = 6

        post_story(
            service_id=story.service_id,
            image_path=media_file,
            link=story.link,
            headless=story.headless,
            num_tabs=num_tabs
        )

        story.updated_at = datetime.now()
        story.story_status = "published_successfully"
        story.webhook_status = "webhook_pending"
        story.webhook_next_attempt = datetime.now()
        story.last_error = None
        story.next_attempt = None
        session.commit()
        print(f"[WORKER] (job_id:{story.id}) Story published successfully")


    except Exception as e:
        story.retries += 1
        next_attempt = calculate_next_attempt(story.retries, story.max_retries)
        if next_attempt:
            story.story_status = "retry_scheduled"
            story.updated_at = datetime.now()
            story.next_attempt = next_attempt
            story.last_error = str(e)
            print(f"[WORKER] (job_id:{story.id}) Story failed: {e}, retry at {next_attempt}")
        else:
            story.story_status = "failed"
            story.updated_at = datetime.now()
            story.webhook_status = "webhook_pending"
            story.webhook_next_attempt = datetime.now()
            story.last_error = str(e)
            print(f"[WORKER] (job_id:{story.id}) Story permanently failed after {story.max_retries} retries")
        session.commit()


def send_webhook(story, webhook_url):
    if story.story_status == "published_successfully":
        success = True
    else:
        success = False

    payload = {
        "service_id": story.service_id,
        "publication_status": story.story_status,
        "http_status": 200 if success else 520,
        "message": (
            "Relacja została pomyślnie opublikowana"
            if success else f"Błąd podczas publikacji relacji: {story.last_error}"
        ),
        "publication_date": story.updated_at.strftime("%Y-%m-%d %H:%M:%S") if success else None
    }

    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code == 200 and r.text.strip() == "OK":
            print(f"[WEBHOOK] Success sent for job_id={story.id}")
            return True
        else:
            print(f"[WEBHOOK] CMS response invalid: {r.status_code}, {r.text}")
            return False
    except Exception as e:
        print(f"[WEBHOOK] Error sending: {e}")
        return False


def process_webhook(story, session):
    try:
        print(f"[WORKER] (job_id:{story.id}) Processing webhook for {story.service_id}")
        story.webhook_status = "webhook_in_progress"
        session.commit()

        webhook_url = fb_profiles[story.service_id].get("webhook_url")
        if not webhook_url:
            print(f"[WARNING] No webhook_url defined for {story.service_id} in config file")
            return jsonify({"status": "error", "error": f"No webhook_url defined for {story.service_id} in config file"}), 400

        webhook = send_webhook(story, webhook_url)
        if not webhook:
            raise Exception(f"[WARNING] Error webhook/CMS {story.service_id}")

        story.webhook_status = "webhooked_successfully"
        story.webhook_next_attempt = None
        story.webhook_retries = 0

    except Exception as e:
        story.webhook_retries += 1
        next_webhook_attempt = calculate_next_attempt(story.webhook_retries, story.max_retries)
        if next_webhook_attempt:
            story.webhook_status = "webhook_retry_scheduled"
            story.webhook_next_attempt = next_webhook_attempt
            print(f"[WORKER] (job_id:{story.id}) Webhook failed: {e}, retry at {next_webhook_attempt}")
        else:
            story.webhook_status = "webhook_failed"
            story.last_error = str(e)
            print(f"[WORKER] (job_id:{story.id}) Webhook permanently failed after {story.max_retries} retries")
        session.commit()


def main():
    session = SessionLocal()
    while True:
        story = session.query(StoryQueue).filter(
            StoryQueue.story_status.in_(["pending", "retry_scheduled"]),
            StoryQueue.next_attempt <= datetime.now()
        ).order_by(StoryQueue.created_at).first()
        if story:
            process_story(story, session)
        else:
            print("[WORKER] No pending stories or retry_scheduled for this time stories")

        story = session.query(StoryQueue).filter(
            StoryQueue.webhook_status.in_(["webhook_pending", "webhook_retry_scheduled"]),
            StoryQueue.webhook_next_attempt <= datetime.now(),
        ).order_by(StoryQueue.created_at).first()
        if story:
            process_webhook(story, session)
        else:
            print("[WORKER] No pending webhooks or retry_scheduled for this time webhooks")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

import random
import time
from flask import jsonify
from datetime import datetime, timedelta, timezone
from db import SessionLocal, engine
from models import Base, StoryQueue
from playwright_bot_stories import (
    post_story,
    download_image,
    validate_image_from_url,
    load_config
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
        story.status = "in_progress"
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

        instagram = fb_profiles[story.service_id].get("has_instagram")
        if instagram is True:
            num_tabs =  8
        else:
            num_tabs = 6

        post_story(
            service_id=story.service_id,
            image_path=image_file,
            link=story.link,
            headless=story.headless,
            num_tabs=num_tabs
        )

        story.status = "published_successfully"
        story.last_error = None
        story.next_attempt = None
        session.commit()
        print(f"[WORKER] (job_id:{story.id}) Story published successfully")


    except Exception as e:
        story.retries += 1
        next_attempt = calculate_next_attempt(story.retries, story.max_retries)
        if next_attempt:
            story.status = "retry_scheduled"
            story.next_attempt = next_attempt
            story.last_error = str(e)
            print(f"[WORKER] (job_id:{story.id}) Story failed: {e}, retry at {next_attempt}")
        else:
            story.status = "failed"
            story.last_error = str(e)
            print(f"[WORKER] (job_id:{story.id}) Story permanently failed after {story.max_retries} retries")
        session.commit()


def main():
    session = SessionLocal()
    while True:
        story = session.query(StoryQueue).filter(
            StoryQueue.status.in_(["pending", "retry_scheduled"]),
            StoryQueue.next_attempt <= datetime.now()
        ).order_by(StoryQueue.created_at).first()
        if story:
            process_story(story, session)
        else:
            print("[WORKER] No pending stories or retry_scheduled for this time stories")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

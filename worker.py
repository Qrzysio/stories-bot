import time
from db import SessionLocal, engine
from models import Base, StoryQueue
from playwright_bot_stories import post_story

Base.metadata.create_all(engine)

CHECK_INTERVAL = 30

def process_story(story, session):
    try:
        print(f"[WORKER] Processing story {story.id} for {story.service_id}")
        story.status = "in_progress"
        session.commit()

        # Вызов твоего бота
        post_story(
            service_id=story.service_id,
            image_path=story.image_url,  # здесь пока url, потом будем скачивать и хранить как файл
            link=story.link,
            headless=True,
            num_tabs=8
        )

        story.status = "success"
        story.last_error = None
        session.commit()
        print(f"[WORKER] Story {story.id} published successfully")

    except Exception as e:
        story.status = "failed"
        story.last_error = str(e)
        story.retries += 1
        session.commit()
        print(f"[WORKER] Story {story.id} failed: {e}")

def main():
    session = SessionLocal()
    while True:
        story = session.query(StoryQueue).filter(StoryQueue.status == "pending").order_by(StoryQueue.created_at).first()
        if story:
            process_story(story, session)
        else:
            print("[WORKER] No pending stories")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

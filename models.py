from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from db import Base

class StoryQueue(Base):
    __tablename__ = "story_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    link = Column(String)
    story_status = Column(String, default="pending")  # pending, in_progress, retry_scheduled, published_successfully, failed
    headless = Column(Boolean, nullable=False, default=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    next_attempt = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    last_error = Column(Text)
    webhook_retries = Column(Integer, default=0)
    webhook_next_attempt = Column(DateTime)
    format = Column(String)  # image | video
    webhook_status = Column(String) # webhook_pending, webhook_in_progress, webhook_retry_scheduled, webhooked_successfully, webhook_failed

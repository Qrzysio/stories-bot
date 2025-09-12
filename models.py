from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from db import Base

class StoryQueue(Base):
    __tablename__ = "story_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_id = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    link = Column(String)
    status = Column(String, default="pending")  # pending, in_progress, retry_scheduled, success, webhook_pending, completed, failed, webhook_failed
    headless = Column(Boolean, nullable=False, default=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=5)
    next_attempt = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_error = Column(Text)
    webhook_tries = Column(Integer, default=0)
    webhook_next_attempt = Column(DateTime)

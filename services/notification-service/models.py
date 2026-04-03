from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(64), index=True)
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)

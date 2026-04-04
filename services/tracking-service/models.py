from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from database import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String(64), index=True)
    status = Column(String(50))
    location = Column(String(200))
    note = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)

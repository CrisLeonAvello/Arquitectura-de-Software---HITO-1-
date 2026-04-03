from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tracking_code = Column(String(64), unique=True, index=True)
    title = Column(String(200))
    description = Column(String(500))
    origin = Column(String(200))
    destination = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import json
import redis
import uvicorn
import os

from database import engine, get_db, Base
from models import TrackingEvent

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tracking Service",
    description="Microservicio de trazabilidad de paquetes",
    version="1.0.0"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
except Exception as e:
    print(f"Advertencia: No se pudo conectar a Redis: {e}")
    redis_client = None


class StatusUpdate(BaseModel):
    tracking_code: str
    status: str
    location: str
    note: str = ""


class TrackingEventResponse(BaseModel):
    id: int
    tracking_code: str
    status: str
    location: str
    note: str
    recorded_at: datetime

    class Config:
        from_attributes = True


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "tracking-service"}


@app.post("/updateStatus")
async def update_status(update: StatusUpdate, db: Session = Depends(get_db)):
    """Actualizar el estado de un paquete y publicar evento a Redis"""
    try:
        event = TrackingEvent(
            tracking_code=update.tracking_code,
            status=update.status,
            location=update.location,
            note=update.note
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        if redis_client:
            try:
                event_data = {
                    "id": event.id,
                    "tracking_code": event.tracking_code,
                    "status": event.status,
                    "location": event.location,
                    "note": event.note,
                    "recorded_at": event.recorded_at.isoformat()
                }
                redis_client.publish("status_updates", json.dumps(event_data))
            except Exception as e:
                print(f"Error publicando a Redis: {e}")

        return {
            "id": event.id,
            "tracking_code": event.tracking_code,
            "status": event.status,
            "location": event.location,
            "note": event.note,
            "recorded_at": event.recorded_at.isoformat(),
            "message": "Estado actualizado exitosamente"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getTracking/{tracking_code}")
async def get_tracking(tracking_code: str, db: Session = Depends(get_db)):
    """Obtener historial de eventos de un paquete"""
    try:
        events = db.query(TrackingEvent).filter(
            TrackingEvent.tracking_code == tracking_code
        ).order_by(TrackingEvent.recorded_at.desc()).all()

        if not events:
            return {
                "tracking_code": tracking_code,
                "events": [],
                "total": 0,
                "message": "Paquete no encontrado"
            }

        return {
            "tracking_code": tracking_code,
            "events": [
                {
                    "id": event.id,
                    "status": event.status,
                    "location": event.location,
                    "note": event.note,
                    "at": event.recorded_at.isoformat()
                }
                for event in events
            ],
            "total": len(events)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)

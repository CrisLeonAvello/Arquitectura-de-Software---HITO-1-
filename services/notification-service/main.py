from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import json
import redis
import threading
import uvicorn
import os

from database import engine, get_db, Base
from models import Notification

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Notification Service",
    description="Microservicio consumidor de eventos de notificación",
    version="1.0.0"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = None
consumer_thread = None


def init_redis_consumer():
    """Inicializar consumidor de eventos Redis"""
    global redis_client
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        print(f"✓ Conectado a Redis en {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"✗ Error conectando a Redis: {e}")
        redis_client = None


def consume_events():
    """Consumidor de eventos de Redis en background"""
    if not redis_client:
        print("✗ Redis no disponible. Consumidor no iniciado.")
        return

    pubsub = redis_client.pubsub()
    pubsub.subscribe("status_updates")
    print("✓ Consumidor escuchando eventos en canal 'status_updates'")

    for message in pubsub.listen():
        if message["type"] == "message":
            try:
                event_data = json.loads(message["data"])
                print(f"✓ Evento recibido: {event_data['tracking_code']} - {event_data['status']}")

                db = next(get_db())
                try:
                    notification_message = (
                        f"Paquete {event_data['tracking_code']} "
                        f"está en estado '{event_data['status']}' "
                        f"en {event_data['location']}"
                    )
                    notification = Notification(
                        tracking_code=event_data["tracking_code"],
                        message=notification_message
                    )
                    db.add(notification)
                    db.commit()
                    print(f"✓ Notificación guardada para {event_data['tracking_code']}")
                except Exception as e:
                    print(f"✗ Error guardando notificación: {e}")
                    db.rollback()
                finally:
                    db.close()
            except json.JSONDecodeError as e:
                print(f"✗ Error decodificando evento: {e}")
            except Exception as e:
                print(f"✗ Error procesando evento: {e}")


@app.on_event("startup")
async def startup_event():
    """Inicializar Redis y consumidor al iniciar la aplicación"""
    global consumer_thread
    init_redis_consumer()

    if redis_client:
        consumer_thread = threading.Thread(target=consume_events, daemon=True)
        consumer_thread.start()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "notification-service"}


@app.get("/getNotifications/{tracking_code}")
async def get_notifications(tracking_code: str, db: Session = Depends(get_db)):
    """Obtener notificaciones registradas para un paquete"""
    try:
        notifications = db.query(Notification).filter(
            Notification.tracking_code == tracking_code
        ).order_by(Notification.sent_at.desc()).all()

        return {
            "tracking_code": tracking_code,
            "notifications": [
                {
                    "id": notif.id,
                    "message": notif.message,
                    "sent_at": notif.sent_at.isoformat()
                }
                for notif in notifications
            ],
            "total": len(notifications)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)

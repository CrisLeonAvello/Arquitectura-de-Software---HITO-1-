from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
import uvicorn

from database import engine, get_db, Base
from models import Package
from utils import generate_tracking_code

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Package Service",
    description="Microservicio de gestión de paquetes",
    version="1.0.0"
)

USER_SERVICE_URL = "http://user-service:8001"


class PackageCreate(BaseModel):
    user_id: int
    title: str
    description: str
    origin: str
    destination: str


class PackageResponse(BaseModel):
    id: int
    user_id: int
    tracking_code: str
    title: str
    description: str
    origin: str
    destination: str

    class Config:
        from_attributes = True


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "package-service"}


@app.post("/createPackage")
async def create_package(package: PackageCreate, db: Session = Depends(get_db)):
    """Crear un nuevo paquete validando que el usuario existe"""
    try:
        httpx_client = httpx.Client()
        try:
            user_response = httpx_client.get(
                f"{USER_SERVICE_URL}/validateUser/{package.user_id}"
            )
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail="Usuario no existe"
                )
        except httpx.RequestError:
            raise HTTPException(
                status_code=503,
                detail="No se pudo validar el usuario (User Service no disponible)"
            )
        finally:
            httpx_client.close()

        existing_package = (
            db.query(Package)
            .filter(
                Package.user_id == package.user_id,
                Package.title == package.title,
                Package.description == package.description,
                Package.origin == package.origin,
                Package.destination == package.destination,
            )
            .first()
        )
        if existing_package:
            raise HTTPException(
                status_code=409,
                detail="No puedes crear mas de un paquete con las mismas caracteristicas"
            )

        tracking_code = generate_tracking_code()
        while db.query(Package).filter(Package.tracking_code == tracking_code).first():
            tracking_code = generate_tracking_code()

        new_package = Package(
            user_id=package.user_id,
            tracking_code=tracking_code,
            title=package.title,
            description=package.description,
            origin=package.origin,
            destination=package.destination
        )
        db.add(new_package)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="No puedes crear mas de un paquete con las mismas caracteristicas"
            )
        db.refresh(new_package)

        return {
            "id": new_package.id,
            "user_id": new_package.user_id,
            "tracking_code": new_package.tracking_code,
            "title": new_package.title,
            "description": new_package.description,
            "origin": new_package.origin,
            "destination": new_package.destination,
            "message": "Paquete creado exitosamente"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getAllPackages")
async def get_all_packages(db: Session = Depends(get_db)):
    """Obtener lista de todos los paquetes"""
    try:
        packages = db.query(Package).all()
        return {
            "packages": [
                {
                    "id": pkg.id,
                    "user_id": pkg.user_id,
                    "tracking_code": pkg.tracking_code,
                    "title": pkg.title,
                    "description": pkg.description,
                    "origin": pkg.origin,
                    "destination": pkg.destination
                }
                for pkg in packages
            ],
            "total": len(packages)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)

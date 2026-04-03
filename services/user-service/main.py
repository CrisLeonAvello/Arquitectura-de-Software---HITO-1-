from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn

from database import engine, get_db, Base
from models import User

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Service",
    description="Microservicio de gestión de usuarios",
    version="1.0.0"
)


class UserCreate(BaseModel):
    username: str
    email: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


class UserList(BaseModel):
    id: int
    username: str
    email: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "user-service"}


@app.post("/createUser")
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario"""
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Usuario ya existe")

        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email ya existe")

        new_user = User(username=user.username, email=user.email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "message": "Usuario creado exitosamente"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getUsers")
async def get_users(db: Session = Depends(get_db)):
    """Obtener lista de todos los usuarios"""
    try:
        users = db.query(User).all()
        return {
            "users": [
                {"id": user.id, "username": user.username, "email": user.email}
                for user in users
            ],
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/validateUser/{user_id}")
async def validate_user(user_id: int, db: Session = Depends(get_db)):
    """Validar que un usuario existe (para Package Service)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"id": user.id, "username": user.username, "email": user.email}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

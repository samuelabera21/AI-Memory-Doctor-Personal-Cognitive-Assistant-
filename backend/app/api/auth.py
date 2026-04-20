from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.database import SessionLocal
from app.models.user_model import User

from app.services.auth_service import hash_password, verify_password
from app.services.jwt_service import create_access_token

router = APIRouter()


class RegisterInput(BaseModel):
    email: str
    password: str


@router.post("/register")
def register(data: RegisterInput):
    if len(data.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters")

    db = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == data.email).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")

        user = User(
            email=data.email.strip().lower(),
            hashed_password=hash_password(data.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return {"message": "User created", "user_id": user.id}
    finally:
        db.close()


class LoginInput(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginInput):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == data.email.strip().lower()).first()
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token = create_access_token({"user_id": user.id})
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    finally:
        db.close()
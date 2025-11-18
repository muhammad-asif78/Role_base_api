# app/auth/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token
from app.dependencies.auth import get_current_user
from app.schemas import user as user_schema
# Use user_schema.UserRead, user_schema.UserCreate

router = APIRouter()
bearer = HTTPBearer()


# ---------------- Models ----------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------- Register ----------------
@router.post("/register", status_code=201)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already registered")

    new_user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered", "user_id": new_user.id}


# ---------------- Login (password -> token) ----------------
@router.post("/token", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    token = create_access_token({
        "id": user.id,
        "email": user.email,
        "role": user.role,
    })

    return {"access_token": token, "token_type": "bearer"}


# ---------------- Get current user ----------------
@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

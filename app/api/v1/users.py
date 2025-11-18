from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.models.user import User, UserRole
from app.schemas import user as user_schema
from app.core.database import get_db
from app.core import security
from app.dependencies.auth import require_role, get_current_user

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

# -----------------------------
# CREATE USER
# -----------------------------
@router.post("/", response_model=user_schema.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: user_schema.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Example role-based restriction
    if current_user.role == UserRole.CTO:
        raise HTTPException(
            status_code=403,
            detail="CTO cannot create users"
        )

    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = security.hash_password(user_in.password)
    new_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# -----------------------------
# GET ALL USERS
# -----------------------------
@router.get("/", response_model=List[user_schema.UserRead])
def get_all_users(
    db: Session = Depends(get_db),
    current_user=Depends(require_role([UserRole.CEO, UserRole.CTO, UserRole.ProjectLead]))
):
    users = db.query(User).all()
    return users

# -----------------------------
# GET SINGLE USER BY ID
# -----------------------------
@router.get("/{user_id}", response_model=user_schema.UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Engineer can only view themselves
    if current_user["role"] == UserRole.Engineer and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Engineers can only view their own profile")

    return user_obj

# -----------------------------
# UPDATE USER
# -----------------------------
@router.patch("/{user_id}", response_model=user_schema.UserRead)
def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # CEO can update all, ProjectLead cannot update, Engineer can update only themselves
    if current_user["role"] == UserRole.ProjectLead:
        raise HTTPException(status_code=403, detail="ProjectLead cannot update users")
    if current_user["role"] == UserRole.Engineer and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Engineers can only update their own profile")

    if user_update.email:
        existing_email_user = db.query(User).filter(User.email == user_update.email, User.id != user_id).first()
        if existing_email_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        user_obj.email = user_update.email

    if user_update.password:
        user_obj.hashed_password = security.hash_password(user_update.password)

    if user_update.role:
        if user_update.role not in UserRole.__members__:
            raise HTTPException(status_code=400, detail="Invalid role")
        user_obj.role = UserRole[user_update.role]

    db.commit()
    db.refresh(user_obj)
    return user_obj

# -----------------------------
# DELETE USER
# -----------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role([UserRole.CEO]))
):
    user_obj = db.query(User).filter(User.id == user_id).first()
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user_obj)
    db.commit()
    return {"detail": "User deleted successfully"}

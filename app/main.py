# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, users
from app.dependencies.auth import get_current_user, require_role

from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Role-Based FastAPI",
    description="Token login + Role-based access",
    version="1.0.0"
)

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------- Routers --------------------
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


@app.get("/")
def root():
    return {"message": "Role-Based FastAPI is running!"}

@app.get("/profile")
def profile(current_user=Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.email}",
        "id": current_user.id,
        "role": current_user.role
    }

@app.get("/admin")
def admin_area(current_user=Depends(require_role(["CEO", "CTO"]))):
    return {"message": f"Admin Access Granted: {current_user.email}"}

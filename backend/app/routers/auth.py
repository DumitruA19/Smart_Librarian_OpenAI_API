# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.core.db import get_db
from app.models import sql_models as m
from app.models.schema import UserCreate, Token, UserOut
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user.
    Stores password hash as VARBINARY(256) (bytes) in SQL Server.
    """
    existing = db.query(m.User).filter(m.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = m.User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),  # bytes → VARBINARY
        role=payload.role,
        created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Validate credentials and return JWT.
    """
    user = db.query(m.User).filter(m.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(str(user.id))
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: m.User = Depends(get_current_user)):
    """
    Return the currently authenticated user.
    Requires Bearer token in Authorization header.
    """
    return current_user

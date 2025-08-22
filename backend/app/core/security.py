# app/core/security.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.models import sql_models as m

settings = get_settings()

# Bcrypt via passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Swagger /docs "Authorize" support (HTTP Bearer)
bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------
# Password hashing utilities
# ---------------------------
def hash_password(plain_password: str) -> bytes:
    """
    Return bytes suitable for VARBINARY(256).
    Passlib returns a string like `$2b$12$...` which we UTF-8 encode to bytes.
    """
    hashed_str = pwd_context.hash(plain_password)
    return hashed_str.encode("utf-8")


def verify_password(plain_password: str, stored_hash: bytes | str | None) -> bool:
    """
    Accepts VARBINARY(256) (bytes) from DB or str for safety.
    """
    if not stored_hash:
        return False
    if isinstance(stored_hash, (bytes, bytearray)):
        stored_hash_str = stored_hash.decode("utf-8", errors="ignore")
    else:
        stored_hash_str = stored_hash
    return pwd_context.verify(plain_password, stored_hash_str)


# ---------------------------
# JWT helpers
# ---------------------------
def create_access_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": sub, "iat": int(datetime.utcnow().timestamp())}
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload.get("sub")
    except JWTError:
        return None


# ---------------------------
# Current user dependency
# ---------------------------
def get_current_user(
    creds: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> m.User:
    """
    Extracts user from Authorization: Bearer <token>.
    Use in protected endpoints: Depends(get_current_user)
    """
    if creds is None or (creds.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user_id = decode_token(creds.credentials)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    # users.id is UNIQUEIDENTIFIER -> map to string; SQLAlchemy will coerce to GUID
    user = db.query(m.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

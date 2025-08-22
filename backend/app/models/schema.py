# app/models/schema.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =========================
# AUTH
# =========================

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str = "user"  # default role


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# =========================
# CHAT / CONVERSATIONS
# =========================

class ConversationCreate(BaseModel):
    title: Optional[str] = None


class ConversationOut(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    conversation_id: UUID
    role: str  # "user" | "assistant" | "tool"
    content: str


class MessageOut(BaseModel):
    id: int  # BIGINT IDENTITY
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# class ChatRequest(BaseModel):
#     """
#     Request-ul minim acceptat de /chat:
#       - message: textul utilizatorului
#       - conversation_id: opțional (poate fi UUID sau string UUID)
#       - metadata: opțional (filtre pentru RAG: ex. {"genre":{"$eq":"fantasy"}})
#       - history: opțional (pentru UI-uri care trimit ultimele mesaje)
#     """
#     message: str = Field(min_length=1)
#     conversation_id: Optional[Union[str, UUID]] = None
#     metadata: Optional[Dict[str, Any]] = None
#     history: Optional[List[Dict[str, str]]] = None
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[Dict[str, str]]] = None  # [{"role":"user/assistant/system","content":"..."}]
    conversation_id: Optional[UUID] = None
    # FE poate trimite oricare din câmpurile de mai jos; serverul le tratează la fel
    metadata: Optional[Dict] = None
    where: Optional[Dict] = None

    # @field_validator("conversation_id")
    # @classmethod
    # def _coerce_uuid(cls, v):
    #     if v in (None, "", "null"):
    #         return None
    #     try:
    #         return UUID(str(v))
    #     except Exception:
    #         raise ValueError("conversation_id must be a UUID string")

class ChatResponse(BaseModel):
    conversation_id: UUID
    answer: str
    title: Optional[str] = None
    reason: Optional[str] = None


# =========================
# RECOMMENDATIONS / FAVORITES
# =========================

class RecommendationOut(BaseModel):
    id: int  # BIGINT IDENTITY
    conversation_id: UUID
    book_title: str
    chroma_doc_id: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteCreate(BaseModel):
    book_title: str
    note: Optional[str] = None


class FavoriteOut(BaseModel):
    id: int
    user_id: UUID
    book_title: str
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# =========================
# SETTINGS
# =========================

class SettingsUpsert(BaseModel):
    tts_enabled: Optional[bool] = None
    stt_enabled: Optional[bool] = None
    language: Optional[str] = Field(default=None, max_length=20)


class SettingsOut(BaseModel):
    user_id: UUID
    tts_enabled: bool
    stt_enabled: bool
    language: Optional[str] = None

    model_config = {"from_attributes": True}


# =========================
# COMMON PAGINATION (optional)
# =========================

class PageMeta(BaseModel):
    total: int
    page: int
    size: int


class PageMessages(BaseModel):
    items: List[MessageOut]
    meta: PageMeta

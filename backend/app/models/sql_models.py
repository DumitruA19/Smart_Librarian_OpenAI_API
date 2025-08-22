# app/models/sql_models.py
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Text, ForeignKey, BigInteger, Boolean, Index
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, VARBINARY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from app.core.db import Base  # asumat existent: declarative_base() în app.core.db

# USERS (PK: UNIQUEIDENTIFIER)
class User(Base):
    __tablename__ = "users"

    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
        index=True,
    )
    email = Column(String(320), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=True)
    password_hash = Column(VARBINARY(256), nullable=False)
    role = Column(String(50), nullable=False, server_default=text("'user'"))
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all,delete",
        passive_deletes=True,
    )

# CONVERSATIONS (PK: UNIQUEIDENTIFIER; FK: users.id)
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(
        UNIQUEIDENTIFIER,
        primary_key=True,
        server_default=text("NEWID()"),
    )
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=True)
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all,delete", passive_deletes=True
    )
    recommendations = relationship(
        "Recommendation", cascade="all,delete", passive_deletes=True
    )

# MESSAGES (PK: BIGINT IDENTITY; FK: conversations.id)
class Message(Base):
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'tool'
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

    conversation = relationship("Conversation", back_populates="messages")

# RECOMMENDATIONS (PK: BIGINT IDENTITY; FK: conversations.id)
class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_title = Column(String(400), nullable=False)
    chroma_doc_id = Column(String(200), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

# FAVORITES (PK: BIGINT IDENTITY; FK: users.id)
class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    book_title = Column(String(400), nullable=False)
    note = Column(String(500), nullable=True)
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

# SETTINGS (PK & FK: users.id)
class Setting(Base):
    __tablename__ = "settings"

    user_id = Column(
        UNIQUEIDENTIFIER,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tts_enabled = Column(Boolean, nullable=False, server_default=text("0"))
    stt_enabled = Column(Boolean, nullable=False, server_default=text("0"))
    language = Column(String(20), nullable=True)

# LOGS (PK: BIGINT IDENTITY; FK: users.id nullable)
class Log(Base):
    __tablename__ = "logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(UNIQUEIDENTIFIER, nullable=True, index=True)
    action = Column(String(100), nullable=False)
    meta = Column(Text, nullable=True)  # redenumit din 'metadata' pentru compatibilitate SQLAlchemy
    created_at = Column(
        DateTime, nullable=False, server_default=text("SYSUTCDATETIME()")
    )

# Indexuri conform scriptului SQL
Index("IX_conversations_user", Conversation.user_id, Conversation.created_at.desc())
Index("IX_messages_conversation", Message.conversation_id, Message.created_at)
Index(
    "IX_recommendations_conversation",
    Recommendation.conversation_id,
    Recommendation.created_at.desc(),
)
Index("IX_favorites_user", Favorite.user_id, Favorite.created_at.desc())
Index("IX_logs_user_time", Log.user_id, Log.created_at.desc())

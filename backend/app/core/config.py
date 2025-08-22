# app/core/config.py
from __future__ import annotations

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError


class Settings(BaseSettings):
    # === Database (SQL Server) ===
    SQLSERVER_CONN_STR: str = Field(..., description="ODBC connection string")

    # === Providers / APIs ===
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")

    # === Auth / JWT ===
    JWT_SECRET: str = Field(..., description="JWT secret")
    JWT_ALG: str = Field("HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, description="JWT expiry minutes")

    # === RAG / ChromaDB ===
    CHROMA_DIR: str = Field("./chroma_store", description="ChromaDB persistence directory")
    COLLECTION_NAME: str = Field("books", description="Default Chroma collection name")

    # === Models (names kept in env for flexibility) ===
    EMBED_MODEL: str = Field("text-embedding-3-small", description="Embedding model name")
    CHAT_MODEL: str = Field("gpt-4o-mini", description="Chat model name")

    # === CORS ===
    CORS_ORIGINS: str = Field(
        "http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed origins",
    )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # ignore unknown env vars instead of failing hard

    @property
    def database_url(self) -> str:
        import urllib.parse
        return "mssql+pyodbc:///?odbc_connect=" + urllib.parse.quote_plus(self.SQLSERVER_CONN_STR)


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as e:
        missing = ", ".join(err.get("loc")[0] for err in e.errors() if err.get("type") == "missing")
        extras = ", ".join(err.get("loc")[0] for err in e.errors() if "extra_forbidden" in err.get("type", ""))
        parts = []
        if missing:
            parts.append(f"Missing required environment variables: {missing}")
        if extras:
            parts.append(f"Unknown environment variables (ignored or add fields): {extras}")
        raise RuntimeError(" | ".join(parts) or str(e))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.routers import auth, chat
import langdetect  # <-- import direct
import threading
import time
from app.rag.ingest import ingest
from pathlib import Path

settings = get_settings()
app = FastAPI(title="Smart Librarian API")

# Forțăm încărcarea profilelor langdetect la startup
_ = langdetect.detect("Aceasta este o propoziție de test.")
print("[INFO] LangDetect profiles preloaded.")

# Configurare CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routere
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

def auto_ingest(interval=600):
    last_mtime = None
    data_path = Path(__file__).parent.parent / "data" / "summaries.json"
    while True:
        try:
            mtime = data_path.stat().st_mtime
            if last_mtime is None or mtime != last_mtime:
                print("[INFO] Detected change in summaries.json, running ingest...")
                ingest()
                last_mtime = mtime
        except Exception as e:
            print(f"[ERROR] Auto-ingest failed: {e}")
        time.sleep(interval)

# Pornește thread-ul la startup
threading.Thread(target=auto_ingest, daemon=True).start()

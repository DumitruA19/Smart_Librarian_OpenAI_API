# chroma_inspect.py
from app.core.config import get_settings
import chromadb
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

settings = get_settings()
client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
collection = client.get_or_create_collection(name=settings.COLLECTION_NAME)

def show_all(limit=None):
    # Returnează primele N documente din colecție
    results = collection.get(limit=limit)
    docs = results.get('documents', [])
    if not docs:
        print("[INFO] Nu există documente în ChromaDB.")
        return
    for i, doc in enumerate(docs):
        print(f"[{i}] {doc}")
        meta = results.get('metadatas', [{}])[i]
        print(f"    meta: {meta}")
        print(f"    id: {results.get('ids', [None])[i]}")

if __name__ == "__main__":
    show_all(10)

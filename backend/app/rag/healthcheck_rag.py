from __future__ import annotations
import argparse
import json
from typing import List, Dict, Any

import chromadb

from app.core.config import get_settings
from app.rag.retriever import similar


def hr(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def list_titles(client: chromadb.api.client.ClientAPI, name: str, limit: int = 50) -> List[Dict[str, Any]]:
    col = client.get_or_create_collection(name=name)
    total = col.count()
    items = []
    offset, page = 0, min(1000, limit)
    while len(items) < limit:
        res = col.get(limit=page, offset=offset)
        ids = res.get("ids", [])
        if not ids:
            break
        docs = res.get("documents", [])
        metas = res.get("metadatas", [])
        for i in range(len(ids)):
            mi = (metas[i] or {}) if i < len(metas) else {}
            di = docs[i] if i < len(docs) else ""
            items.append({
                "id": ids[i],
                "title": mi.get("title"),
                "genre": mi.get("genre"),
                "lang": mi.get("lang"),
                "chunk": mi.get("chunk"),
                "preview": (di[:160] + ("…" if di and len(di) > 160 else "")) if di else "",
            })
            if len(items) >= limit:
                break
        offset += len(ids)
        if len(ids) == 0:
            break
    return {"items": items, "total": total}


def run_healthcheck(list_limit: int, queries: List[str], k: int, where_json: str | None) -> int:
    settings = get_settings()
    client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))

    hr("Chroma settings")
    print("CHROMA_DIR        :", settings.CHROMA_DIR)
    print("COLLECTION_NAME   :", settings.COLLECTION_NAME)
    print("EMBED_MODEL       :", settings.EMBED_MODEL)

    col = client.get_or_create_collection(settings.COLLECTION_NAME)
    total = col.count()
    print("COLLECTION COUNT  :", total)

    if total == 0:
        print("[WARN] Colecția este goală. Verifică ingest-ul și calea CHROMA_DIR.")
        # continuăm, ca să nu stricăm exit code-ul în CI; folositor local

    # --- Listare titluri ---
    hr(f"Primele {min(list_limit, total)} iteme (titluri unice)")
    res = list_titles(client, settings.COLLECTION_NAME, limit=min(list_limit, max(total, list_limit)))
    seen = set()
    idx = 1
    for it in res["items"]:
        t = it.get("title") or "(fără titlu)"
        if t in seen:
            continue
        seen.add(t)
        print(f"{idx:>2}. {t} [lang={it.get('lang')}, genre={it.get('genre')}, chunk={it.get('chunk')}] ")
        idx += 1
        if idx > list_limit:
            break

    # --- Teste de interogare ---
    where = None
    if where_json:
        try:
            where = json.loads(where_json)
        except Exception as e:
            print(f"[WARN] Ignor --where invalid: {e}")

    failed = 0
    hr("Interogări de test (RAG)")
    for q in queries:
        hits = similar(q, k=k, where=where)
        docs = (hits.get("documents") or [[]])[0]
        metas = (hits.get("metadatas") or [[]])[0]
        titles = [ (m or {}).get("title") for m in metas ]
        print(f"Q: {q}")
        print("   -> docs:", len(docs), "| titluri:", titles[:k])
        if not docs:
            failed += 1

    if failed:
        hr("Rezultat")
        print(f"[WARN] {failed} din {len(queries)} interogări nu au returnat contexte. Verifică ingest/retriever sau filtrele (where).")
        # return 1  # Dacă vrei cod non-zero la eșec
    else:
        hr("Rezultat")
        print("OK: toate interogările au primit contexte.")

    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Healthcheck pentru RAG/Chroma la Smart Librarian")
    p.add_argument("--list", dest="list_limit", type=int, default=30, help="Câte titluri să listeze (default 30)")
    p.add_argument("--queries", nargs="*", default=[
        "o carte despre prietenie",
        "dystopian novel about freedom",
        "fantasy pentru toate vârstele"
    ], help="Întrebări de test pentru RAG")
    p.add_argument("--k", type=int, default=6, help="Numărul de pasaje de returnat per query")
    p.add_argument("--where", dest="where_json", type=str, default=None, help='Filtru JSON Chroma, ex: "{\"lang\":\"ro\"}"')
    args = p.parse_args()

    exit(run_healthcheck(args.list_limit, args.queries, args.k, args.where_json))

from __future__ import annotations
from typing import Any, Dict, Optional, List, Tuple
import time
from collections import defaultdict

import chromadb
try:
    from rank_bm25 import BM25Okapi  # optional
except Exception:
    BM25Okapi = None

from app.core.config import get_settings
from app.core.openai_client import embed

settings = get_settings()
client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
collection = client.get_or_create_collection(name=settings.COLLECTION_NAME)

# ------- tiny in-memory TTL cache -------
_CACHE: dict[str, Tuple[float, dict]] = {}
_TTL_SECONDS = 600  # 10 minutes


def _key(query: str, k: int, where: Optional[Dict[str, Any]]) -> str:
    return f"{query.strip().lower()}|k={k}|where={where}"


def _get_cached(key: str):
    v = _CACHE.get(key)
    if not v:
        return None
    ts, data = v
    if time.time() - ts > _TTL_SECONDS:
        _CACHE.pop(key, None)
        return None
    return data


def _set_cached(key: str, data: dict):
    _CACHE[key] = (time.time(), data)


# ------- MMR diversity (approx) -------
def _mmr(texts: List[str], scores: List[float], k: int = 6, lam: float = 0.3) -> List[int]:
    tokens = [set((t or "").lower().split()) for t in texts]
    selected, rest = [], list(range(len(texts)))
    while rest and len(selected) < min(k, len(texts)):
        best, best_score = None, float("-inf")
        for i in rest:
            rel = scores[i]
            div = 0.0 if not selected else max(
                (len(tokens[i].intersection(tokens[j])) / (len(tokens[i]) + 1e-9)) for j in selected
            )
            score = lam * rel - (1 - lam) * div
            if score > best_score:
                best, best_score = i, score
        selected.append(best)
        rest.remove(best)
    return selected


def _bm25_ranks(query: str, texts: List[str]) -> Dict[int, int]:
    if not BM25Okapi:
        return {}
    docs = [ (t or "").lower().split() for t in texts ]
    bm25 = BM25Okapi(docs)
    scores = bm25.get_scores((query or "").lower().split())
    order = sorted(range(len(texts)), key=lambda i: scores[i], reverse=True)
    return {idx: rank for rank, idx in enumerate(order, start=1)}


def _rrf(sem_order: List[int], bm25_ranks: Dict[int, int], k: int) -> List[int]:
    fused = defaultdict(float)
    for rank, idx in enumerate(sem_order, start=1):
        fused[idx] += 1.0 / (60 + rank)
    for idx, r in bm25_ranks.items():
        fused[idx] += 1.0 / (60 + r)
    ordered = sorted(fused.keys(), key=lambda i: fused[i], reverse=True)
    return ordered[:k]


def similar(query: str, k: int = 6, where: Optional[Dict[str, Any]] = None) -> dict:
    cache_key = _key(query, k, where)
    cached = _get_cached(cache_key)
    if cached:
        return cached

    vecs = embed([query])
    if not vecs or not vecs[0]:
        empty = {"documents": [[]], "metadatas": [[]], "ids": [[]], "distances": [[]]}
        _set_cached(cache_key, empty)
        return empty

    base_k = max(k * 2, 8)
    args = dict(query_embeddings=vecs, n_results=base_k)
    if where:
        args["where"] = where
    out = collection.query(**args)

    docs = (out.get("documents") or [[]])[0]
    metas = (out.get("metadatas") or [[]])[0]
    ids = (out.get("ids") or [[]])[0]
    dists = (out.get("distances") or [[]])[0] or [0.0] * len(docs)

    if not docs:
        _set_cached(cache_key, out)
        return out

    rel = [ -float(d or 0.0) for d in dists ]  # Chroma distance -> relevance

    mmr_idx = _mmr(docs, rel, k=min(base_k, len(docs)))
    final_idx = mmr_idx

    if BM25Okapi:
        sem_order = sorted(mmr_idx, key=lambda i: rel[i], reverse=True)
        bm25_r = _bm25_ranks(query, docs)
        final_idx = _rrf(sem_order, bm25_r, k)

    final_idx = final_idx[:k]

    result = {
        "documents": [[docs[i] for i in final_idx]],
        "metadatas": [[metas[i] for i in final_idx]],
        "ids":       [[ids[i]   for i in final_idx]],
        "distances": [[dists[i] for i in final_idx]],
    }
    _set_cached(cache_key, result)
    return result

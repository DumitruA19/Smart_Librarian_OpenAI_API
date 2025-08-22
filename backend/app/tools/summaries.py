# app/tools/summaries.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


# Directory-ul standard: backend/data/
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Poți seta în .env: SUMMARY_FILE=book_summaries_20_en_expanded.json
SUMMARY_FILE = os.getenv("SUMMARY_FILE", "summaries.json")

# Calea finală
DATA_JSON = DATA_DIR / SUMMARY_FILE

# Cache intern simplu
_SUMMARIES_CACHE: List[Dict[str, Any]] | None = None


def _load_file() -> List[Dict[str, Any]]:
    """
    Încarcă JSON-ul cu format:
    [
      {"title": "1984", "summary": "...", "genre": "Dystopian"}, ...
    ]
    """
    if not DATA_JSON.exists():
        # fallback: ia primul *.json din data/
        json_candidates = sorted(DATA_DIR.glob("*.json"))
        if not json_candidates:
            raise FileNotFoundError(
                f"Nu am găsit {DATA_JSON} și niciun fișier .json în {DATA_DIR}."
            )
        # folosește primul găsit
        cand = json_candidates[0]
        items = json.loads(cand.read_text("utf-8"))
        if not isinstance(items, list):
            raise ValueError(f"JSON invalid (nu este listă) în {cand}")
        return items

    # calea explicită
    items = json.loads(DATA_JSON.read_text("utf-8"))
    if not isinstance(items, list):
        raise ValueError(f"JSON invalid (nu este listă) în {DATA_JSON}")
    return items


def _ensure_cache() -> None:
    global _SUMMARIES_CACHE
    if _SUMMARIES_CACHE is None:
        _SUMMARIES_CACHE = _load_file()


def reload_cache() -> None:
    """Forțează reîncărcarea fișierului (ex: după ce ai înlocuit summaries.json)."""
    global _SUMMARIES_CACHE
    _SUMMARIES_CACHE = None
    _ensure_cache()


def get_summary_by_title(title: str) -> Optional[str]:
    """
    Returnează rezumatul pentru titlul exact (case-insensitive).
    Dacă nu găsește, întoarce None.
    """
    if not title:
        return None
    _ensure_cache()
    title_norm = title.strip().lower()
    for it in _SUMMARIES_CACHE or []:
        t = str(it.get("title", "")).strip().lower()
        if t == title_norm:
            return it.get("summary")
    return None


def list_titles() -> List[str]:
    """Returnează lista tuturor titlurilor din cache, fără duplicate (case-insensitive, fără spații suplimentare)."""
    _ensure_cache()
    seen = set()
    titles = []
    for it in (_SUMMARIES_CACHE or []):
        t = str(it.get("title", "")).strip()
        t_norm = t.lower()
        if t and t_norm not in seen:
            seen.add(t_norm)
            titles.append(t)
    return titles


def search(
    text: Optional[str] = None,
    genre: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Căutare simplă în colecția locală după:
      - `text` (căutare parțială în title/summary, case-insensitive)
      - `genre` (dacă fișierul are câmpul 'genre'; match case-insensitive exact)
    Întoarce toate rezultatele dacă limit=None.
    """
    _ensure_cache()
    items = _SUMMARIES_CACHE or []

    text_norm = (text or "").strip().lower()
    genre_norm = (genre or "").strip().lower()

    def _ok(it: Dict[str, Any]) -> bool:
        if genre_norm:
            g = str(it.get("genre", "")).lower()
            if g != genre_norm:
                return False
        if text_norm:
            title = str(it.get("title", "")).lower()
            summary = str(it.get("summary", "")).lower()
            if text_norm not in title and text_norm not in summary:
                return False
        return True

    results = [it for it in items if _ok(it)]
    if limit is None:
        return results
    return results[: max(1, limit)]

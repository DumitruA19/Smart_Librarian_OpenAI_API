# app/core/guard.py


from typing import Set
from fastapi import HTTPException, status
from pathlib import Path

def _load_bad_words(path: str = None) -> Set[str]:
    if not path:
        path = str(Path(__file__).parent / "bad_words.txt")
    try:
        with open(path, encoding="utf-8") as f:
            return set(line.strip().lower() for line in f if line.strip() and not line.startswith("#"))
    except Exception:
        return set()

_BAD_WORDS_SET = _load_bad_words()

def input_allowed_or_raise(user_text: str):
    """Blochează dacă textul conține injurii din fișierul bad_words.txt."""
    txt = (user_text or "").strip().lower()
    if not txt:
        return
    for bad in _BAD_WORDS_SET:
        if bad in txt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your message contains offensive language and was blocked.",
            )

def scrub_output(text: str, mask: str = "****") -> str:
    """Înlocuiește cuvintele injurioase cu mask, pe baza bad_words.txt."""
    if not text:
        return text
    out = text
    for bad in _BAD_WORDS_SET:
        out = out.replace(bad, mask)
    return out
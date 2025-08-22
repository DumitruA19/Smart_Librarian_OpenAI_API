# app/routers/chat.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, Tuple, List, Dict
import re
import unicodedata
import os
import chromadb

from app.core.db import get_db
from app.models import sql_models as m
from app.models.schema import ChatRequest, ChatResponse
from app.rag.retriever import similar
from app.tools.summaries import get_summary_by_title
from app.core.openai_client import chat_complete, chat_complete_stream
from app.core.security import get_current_user
from app.core.guard import input_allowed_or_raise
from app.core.config import get_settings

settings = get_settings()
DEBUG = bool(getattr(settings, "DEBUG", False) or os.getenv("DEBUG_RAG") == "1")

router = APIRouter(prefix="/chat", tags=["chat"])

# ---------------- System prompts (RAG strict) ----------------
# SYSTEM_RO = (
#     "Ești Smart Librarian. Răspunde STRICT folosind doar CONTEXTUL furnizat. "
#     "Dacă informația nu este în CONTEXT, spune explicit că nu știi. "
#     "Nu inventa titluri, autori sau detalii."
# )
# ...existing code...
SYSTEM_RO = (
    "Ești Smart Librarian. Folosește contextul furnizat pentru a răspunde, dar dacă nu găsești informații exacte, poți sugera titluri similare sau să explici de ce nu există o recomandare directă."
)
# ...existing code...
SYSTEM_EN = (
    "You are Smart Librarian. Answer STRICTLY using only the provided CONTEXT. "
    "If the answer is not in CONTEXT, say you don't know. "
    "Do not invent titles, authors, or details."
)

# ---------------- Utilitare text ----------------
def _norm_text(s: str) -> str:
    """lower + fără diacritice + spații compacte."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ---------------- Dicționare/regex pentru intenție ----------------
BOOK_TERMS = {
    # RO (fără diacritice – folosim _norm_text)
    "carte", "carti", "roman", "romane", "titlu", "titluri",
    "volum", "volume", "serie", "serii", "trilogie", "saga",
    "autor", "autori", "scriitor", "scriitori", "editor", "editura", "editie",
    "biblioteca", "lectura", "literatura", "capitol", "capitole",
    "personaj", "personaje", "tema", "teme", "gen", "genuri",
    # EN
    "book", "books", "novel", "novels", "title", "titles",
    "volume", "volumes", "series", "trilogy", "saga",
    "author", "authors", "writer", "writers", "publisher", "edition",
    "library", "reading", "literature", "chapter", "chapters",
    "character", "characters", "theme", "themes", "genre", "genres",
}

ACTION_TERMS = {
    # RO (inclus „sugerezi” & co)
    "recomanda", "recomandare", "recomandari", "recomanzi", "recomandati",
    "sugereaza", "sugestie", "sugestii", "propune", "propuneri",
    "arata", "arata-mi", "da-mi", "da mi", "dami", "gaseste", "gasi", "cauta",
    "vreau", "as dori", "imi poti recomanda", "poti recomanda", "merita citita",
    "top", "lista", "ce sa citesc", "ce sa mai citesc", "must read", "de citit",
    "sugerezi", "sugerati", "sugerez", "sugereste",
    # EN
    "recommend", "recommendation", "recommendations", "suggest", "suggestion", "suggestions",
    "propose", "show me", "give me", "find", "search", "looking for", "i want", "i would like",
    "what to read", "good read", "must read", "top", "list",
}

INFO_TERMS = {
    # RO
    "rezumat", "sinopsis", "descriere", "detalii", "informatii",
    "subiect", "poveste", "tema", "teme", "gen", "genul", "tematica",
    "autorul", "cine a scris", "anul aparitiei", "publicata", "pagini",
    "capitole", "editura", "editie", "traducere", "personaje", "finalul",
    "compara cu", "similar cu", "alternative", "carti similare",
    "recenzie", "pareri", "rating", "note",
    # EN
    "summary", "synopsis", "description", "details", "information", "plot", "story",
    "author", "who wrote", "published", "year", "pages", "edition", "publisher",
    "translation", "characters", "ending", "compare with", "similar to", "alternatives",
    "review", "reviews", "opinions", "rating", "score",
}

FOLLOWUP_PATTERNS = [
    # RO (pattern-uri explicite)
    r"\bdespre (ea|el|aceasta carte|cartea asta|cartea aceea)\b",
    r"\b(mai multe )?detalii (despre|legate de)\b",
    r"\bspune[- ]mi (mai multe|detalii) (despre|de)\b",
    r"\brezumat(ul)?( ei| al ei| al cartii| al acestei carti)?\b",
    r"\bautor(ul)?( ei| al ei| al cartii)?\b",
    # EN
    r"\bthis (book|novel)\b", r"\bthat (book|novel)\b",
    r"\babout (it|this|that|the book|the novel)\b",
    r"\bmore details (about|on)\b",
    r"\bsummary (please)?\b",
]
BOOK_REGEX = [re.compile(p, re.IGNORECASE) for p in FOLLOWUP_PATTERNS]

# Hint-uri „loose” pentru follow-up fără „despre …”
FOLLOWUP_HINTS = {
    # RO
    "detalii", "rezumat", "autor", "tema", "subiect", "personaje",
    # EN
    "details", "more details", "summary", "author", "plot", "characters",
}

ALL_BOOKS_RE = re.compile(
    r"^(?:/books|(?:(?:da mi|da-mi|arata|afiseaza|listeaza)\s*)?(?:toate|lista)\s+carti(?:le)?)$"
)

def is_book_related(message: str) -> bool:
    """
    Heuristică robustă:
    - Follow-up patterns -> True
    - altfel: (cel puțin 1 termen de domeniu) AND (intenție SAU informații)
    - include expresii tip „ce sa citesc / what to read”
    """
    n = _norm_text(message)
    if any(rx.search(n) for rx in BOOK_REGEX):
        return True

    has_domain = any(t in n for t in BOOK_TERMS)
    has_intent = any(t in n for t in ACTION_TERMS) or bool(
        re.search(r"\b(ce sa|what (should|to)) (citesc|read)\b", n)
    )
    has_info = any(t in n for t in INFO_TERMS)
    return has_domain and (has_intent or has_info)

# ---------------- Detectare limbă & follow-up ----------------
def _detect_lang(text: str) -> str:
    try:
        import langdetect
        lang = langdetect.detect(text)
    except Exception:
        lang = "en"
    return "ro" if str(lang).startswith("ro") else "en"

def _is_followup_loose(msg: str) -> bool:
    n = _norm_text(msg)
    if any(rx.search(n) for rx in BOOK_REGEX):
        return True
    return any(h in n for h in FOLLOWUP_HINTS)

# ---------------- Utilitare Chroma ----------------
def _list_titles_from_chroma(limit: Optional[int] = None) -> List[str]:
    """Titluri unice din Chroma (ordonate alfabetic)."""
    client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
    c = client.get_or_create_collection(settings.COLLECTION_NAME)
    off, page = 0, 1000
    titles: List[str] = []
    while True:
        res = c.get(limit=page, offset=off)
        ids = res.get("ids", [])
        if not ids:
            break
        metas = res.get("metadatas", [])
        for i in range(len(ids)):
            mi = (metas[i] or {}) if i < len(metas) else {}
            t = mi.get("title")
            if t:
                titles.append(t)
        off += len(ids)
        if limit and len(set(titles)) >= limit:
            break
    return sorted(set(titles), key=lambda s: str(s).lower())

def _is_all_books_query(q: str) -> bool:
    return bool(ALL_BOOKS_RE.match(_norm_text(q)))

def _get_last_recommended_book(conv_id: UUID, db: Session) -> Optional[str]:
    rec = (
        db.query(m.Recommendation)
        .filter(m.Recommendation.conversation_id == conv_id)
        .order_by(m.Recommendation.id.desc())
        .first()
    )
    return rec.book_title if rec else None

def _retrieve_with_fallback(query: str, k: int, where: Optional[Dict], last_book: Optional[str]) -> Tuple[List[str], List[Dict]]:
    """
    1) încearcă RAG cu where={"title": last_book} (dacă există)
    2) fallback: fără where + filtrare pe meta.title SAU pe prefixul documentului ("Title\\n\\n...")
    3) fallback final: caută direct după last_book
    """
    want = (last_book or "").casefold().strip()

    # 1) strict pe titlu (dacă avem)
    where1 = {**(where or {})}
    if last_book:
        where1["title"] = last_book
    hits = similar(query, k=max(k * 2, 8), where=where1 if last_book else (where or None))
    docs = (hits.get("documents") or [[]])[0]
    metas = (hits.get("metadatas") or [[]])[0]
    if docs:
        return docs[:k], metas[:k]

    # 2) fallback soft
    hits2 = similar(query, k=max(k * 2, 16), where=where or None)
    docs2 = (hits2.get("documents") or [[]])[0]
    metas2 = (hits2.get("metadatas") or [[]])[0]

    if docs2:
        if last_book:
            keep = []
            for i, mtd in enumerate(metas2):
                title_meta = (mtd or {}).get("title", "")
                if title_meta and title_meta.casefold().strip() == want:
                    keep.append(i)
                    continue
                di = (docs2[i] or "")
                head = di.split("\n", 1)[0].casefold().strip()
                if want and head.startswith(want):
                    keep.append(i)
            if keep:
                docs2 = [docs2[i] for i in keep]
                metas2 = [metas2[i] for i in keep]

        if docs2:
            return docs2[:k], metas2[:k]

    # 3) ultimul fallback: căutare directă după titlu
    if last_book:
        hits3 = similar(last_book, k=max(k * 2, 12), where=where or None)
        docs3 = (hits3.get("documents") or [[]])[0]
        metas3 = (hits3.get("metadatas") or [[]])[0]
        if docs3:
            return docs3[:k], metas3[:k]

    return [], []

# ------------------------- /chat -------------------------
@router.post("", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    input_allowed_or_raise(req.message)

    # conversația curentă (ultimul chat al userului)
    conv = (
        db.query(m.Conversation)
        .filter(m.Conversation.user_id == current_user.id)
        .order_by(m.Conversation.created_at.desc())
        .first()
    )
    if not conv:
        conv = m.Conversation(user_id=current_user.id, title="New Chat")
        db.add(conv); db.commit(); db.refresh(conv)

    lang = _detect_lang(req.message)
    system_prompt = SYSTEM_RO if lang == "ro" else SYSTEM_EN

    # salvează mesajul userului
    db.add(m.Message(conversation_id=conv.id, role="user", content=req.message))
    db.commit()

    # ---- Comandă: toate cărțile
    if _is_all_books_query(req.message):
        titles = _list_titles_from_chroma()
        answer = (
            "Nu am găsit nicio carte în colecție."
            if not titles else
            (f"Iată toate titlurile ({len(titles)}):\n- " + "\n- ".join(titles)) if lang == "ro"
            else (f"Here are all titles ({len(titles)}):\n- " + "\n- ".join(titles))
        )
        db.add(m.Message(conversation_id=conv.id, role="assistant", content=answer))
        db.add(m.Log(user_id=current_user.id, action="chat"))
        db.commit()
        return ChatResponse(conversation_id=conv.id, answer=answer, title=None, reason=None)

    # ultima carte recomandată în acest chat (o folosim și dacă mesajul nu e detectat ca „book related”)
    last_book = _get_last_recommended_book(conv.id, db)

    # ---- Gard: nu e despre cărți (dar lăsăm follow-up-urile „loose” să treacă dacă avem last_book)
    if not is_book_related(req.message):
        if not (last_book and _is_followup_loose(req.message)):
            answer = "Sunt un bibliotecar virtual și pot discuta doar despre cărți, autori sau recomandări de lectură."
            db.add(m.Message(conversation_id=conv.id, role="assistant", content=answer))
            db.add(m.Log(user_id=current_user.id, action="chat"))
            db.commit()
            return ChatResponse(conversation_id=conv.id, answer=answer, title=None, reason=None)

    # (1) Rezumat local, dacă se cere explicit și avem ultima carte
    if last_book and any(k in _norm_text(req.message) for k in ("rezumat", "summary")):
        summary = get_summary_by_title(last_book)
        db.add(m.Message(conversation_id=conv.id, role="assistant", content=summary))
        db.add(m.Recommendation(conversation_id=conv.id, book_title=last_book, reason=summary))
        db.add(m.Log(user_id=current_user.id, action="chat"))
        db.commit()
        return ChatResponse(conversation_id=conv.id, answer=summary, title=last_book, reason=summary)

    # (2) RAG strict (ancorat pe ultima carte, cu fallback)
    where_filter = getattr(req, "where", None) or getattr(req, "metadata", None) or {}
    rag_query = req.message if not last_book else f"{last_book} {req.message}"
    docs, metas = _retrieve_with_fallback(rag_query, k=6, where=where_filter, last_book=last_book)

    if DEBUG:
        print(f"[FLOW] msg={req.message!r} last={last_book!r} lang={lang}")
        print(f"[RAG] docs={len(docs)} titles={[ (m or {}).get('title') for m in metas ]}")

    if not docs:
        # Fallback prietenos: rezumatul ultimei cărți (dacă există)
        if last_book:
            summary = get_summary_by_title(last_book)
            if summary:
                db.add(m.Message(conversation_id=conv.id, role="assistant", content=summary))
                db.add(m.Recommendation(conversation_id=conv.id, book_title=last_book, reason=summary))
                db.add(m.Log(user_id=current_user.id, action="chat"))
                db.commit()
                return ChatResponse(conversation_id=conv.id, answer=summary, title=last_book, reason=summary)

        answer = "Nu am găsit informații relevante în biblioteca noastră pentru întrebarea ta. Încearcă să reformulezi sau întreabă de un titlu/autor."
        db.add(m.Message(conversation_id=conv.id, role="assistant", content=answer))
        db.add(m.Log(user_id=current_user.id, action="chat"))
        db.commit()
        return ChatResponse(conversation_id=conv.id, answer=answer, title=None, reason=None)

    # Construim contextul pentru LLM
    context = "\n\n".join(
        f"### [{i+1}] {(metas[i] or {}).get('title','(fără titlu)')}\n{docs[i]}"
        for i in range(len(docs))
    )

    messages = [{"role": "system", "content": system_prompt}]
    if getattr(req, "history", None):
        messages += req.history
    messages.append({"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {req.message}"})

    res = chat_complete(messages)
    gpt_answer = res["text"].strip()

    # Extrage titlul din ghilimele; fallback la prima sursă din RAG
    title_match = re.search(r'[\"“”\'‘’]([^\"“”\'‘’]{2,120})[\"“”\'‘’]', gpt_answer)
    book_title = title_match.group(1).strip() if title_match else None

    sources = [ (mtd or {}).get("title") for mtd in metas ]
    sources = [s for s in sources if s]
    sources = list(dict.fromkeys(sources))
    if not book_title and sources:
        book_title = sources[0]

    if book_title:
        db.add(m.Recommendation(conversation_id=conv.id, book_title=book_title, reason=gpt_answer))
    db.add(m.Message(conversation_id=conv.id, role="assistant", content=gpt_answer))
    db.add(m.Log(user_id=current_user.id, action="chat"))
    db.commit()

    return ChatResponse(conversation_id=conv.id, answer=gpt_answer, title=book_title, reason=gpt_answer)

# ------------------------- /chat/stream -------------------------
@router.post("/stream")
def chat_stream(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    input_allowed_or_raise(req.message)

    conv = (
        db.query(m.Conversation)
        .filter(m.Conversation.user_id == current_user.id)
        .order_by(m.Conversation.created_at.desc())
        .first()
    )
    if not conv:
        conv = m.Conversation(user_id=current_user.id, title="New Chat")
        db.add(conv); db.commit(); db.refresh(conv)

    lang = _detect_lang(req.message)
    system_prompt = SYSTEM_RO if lang == "ro" else SYSTEM_EN

    db.add(m.Message(conversation_id=conv.id, role="user", content=req.message))
    db.commit()

    last_book = _get_last_recommended_book(conv.id, db)
    where_filter = getattr(req, "where", None) or getattr(req, "metadata", None) or {}
    rag_query = req.message if not last_book else f"{last_book} {req.message}"
    docs, metas = _retrieve_with_fallback(rag_query, k=6, where=where_filter, last_book=last_book)

    if not docs:
        def gen_empty():
            msg = "Nu am găsit informații relevante în colecție."
            yield f"data: {msg}\n\n"
            yield "event: end\ndata: [DONE]\n\n"
        return StreamingResponse(gen_empty(), media_type="text/event-stream")

    context = "\n\n".join(
        f"### [{i+1}] {(metas[i] or {}).get('title','(fără titlu)')}\n{docs[i]}"
        for i in range(len(docs))
    )
    user_message = f"CONTEXT:\n{context}\n\nQUESTION: {req.message}"

    def gen():
        for delta in chat_complete_stream(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]
        ):
            yield f"data: {delta}\n\n"
        yield "event: end\ndata: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

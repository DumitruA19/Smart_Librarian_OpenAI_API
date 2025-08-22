
# app/core/openai_client.py
from __future__ import annotations
from typing import Iterable, List, Optional, Dict, Generator
import time, json
from openai import OpenAI, APIError, RateLimitError, APITimeoutError
from app.core.config import get_settings

settings = get_settings()
_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# -------- retry util --------
def _retry_call(fn, *args, retries: int = 3, base_delay: float = 0.8, **kwargs):
    attempt = 0
    while True:
        try:
            return fn(*args, **kwargs)
        except (APIError, RateLimitError, APITimeoutError) as e:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(base_delay * (1.6 ** (attempt - 1)))

# -------- embeddings --------
def embed(texts: Iterable[str]) -> List[List[float]]:
    texts = [t if isinstance(t, str) else str(t) for t in texts]
    if not texts:
        return []
    resp = _retry_call(
        _client.embeddings.create,
        model=settings.EMBED_MODEL,  # ex. text-embedding-3-small
        input=texts,
    )
    return [d.embedding for d in resp.data]

# -------- chat (non-stream) --------
def chat_complete(messages: List[Dict], temperature: float = 0.2) -> Dict:
    """
    Folosește Responses API. Returnează dict cu:
    { "text": str, "usage": {"input_tokens": int, "output_tokens": int}, "latency_ms": int }
    """
    # transformare la formatul Responses (text blocks)
    full_messages = []
    for m in messages:
        full_messages.append({
            "role": m["role"],
            "content": [{"type": "input_text", "text": m["content"]}],
        })

    t0 = time.time()
    resp = _retry_call(
        _client.responses.create,
        model=settings.CHAT_MODEL,     # ex. gpt-4o-mini
        input=full_messages,
        temperature=temperature,
        max_output_tokens=500,
    )
    dt = int((time.time() - t0) * 1000)
    usage = getattr(resp, "usage", None)
    return {
        "text": (resp.output_text or "").strip(),
        "usage": {
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
        },
        "latency_ms": dt,
    }

# -------- chat streaming (SSE) --------
def chat_complete_stream(messages: List[Dict], temperature: float = 0.2) -> Generator[str, None, None]:
    """
    Generator care produce bucăți de text. Fiecare yield e un fragment de răspuns.
    """
    full_messages = []
    for m in messages:
        full_messages.append({
            "role": m["role"],
            "content": [{"type": "input_text", "text": m["content"]}],
        })

    with _client.responses.stream(
        model=settings.CHAT_MODEL,
        input=full_messages,
        temperature=0.2,
        max_output_tokens=700,
    ) as stream:
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
        # finalize
        stream.close()

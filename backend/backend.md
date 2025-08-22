# Smart Librarian Backend

## Descriere
Acest proiect este un backend FastAPI care implementează un sistem de recomandare de cărți folosind RAG (Retrieval-Augmented Generation) cu OpenAI și ChromaDB.

- **Utilizatorii** se pot înregistra, autentifica și interacționa cu chatbotul pentru a primi recomandări personalizate de lectură.
- **RAG**: întrebările utilizatorului sunt procesate semantic, se caută cartea relevantă în ChromaDB (vector store), iar răspunsul este generat cu GPT augmentat cu rezumatul cărții.

## Tehnologii folosite
- **FastAPI** — API REST rapid și modern
- **SQL Server** — stocare utilizatori, conversații, mesaje
- **ChromaDB** — stocare vectori pentru căutare semantică
- **OpenAI API** — embeddings și generare răspunsuri
- **Passlib + JWT** — autentificare și securitate

## Structură principală
- `app/routers/auth.py` — înregistrare, login, profil user
- `app/routers/chat.py` — endpoint principal de chat și recomandări
- `app/rag/ingest.py` — ingestie rezumate cărți în ChromaDB
- `app/rag/retriever.py` — căutare semantică în vector store
- `app/tools/summaries.py` — acces rapid la rezumate și titluri
- `app/core/openai_client.py` — integrare cu OpenAI
- `data/summaries.json` — baza de date cu rezumate de cărți

## Flow RAG
1. **Ingestie**: rulează `app/rag/ingest.py` pentru a popula ChromaDB cu embeddings OpenAI pe baza rezumatelor din `summaries.json`.
2. **Chat**: utilizatorul trimite o întrebare; sistemul caută semantic cartea potrivită în ChromaDB.
3. **Augmentare**: se extrage rezumatul și titlul, se trimit ca context la GPT pentru generarea răspunsului.
4. **Răspuns**: utilizatorul primește o recomandare personalizată, salvată în istoricul conversației.

## Funcționalități cheie
- Recomandări de lectură pe baza cererii utilizatorului
- Listare titluri disponibile (prompt: "list all books")
- Autentificare JWT
- Istoric conversații și mesaje

## Cum rulezi
1. Instalează dependențele:
	```bash
	pip install -r requirements.txt
	```
2. Configurează `.env` cu datele SQL Server, OpenAI API key etc.
3. Rulează ingestia:
	```bash
	python -m app.rag.ingest
	```
4. Pornește serverul:
	```bash
	uvicorn app.main:app --reload
	```
5. Accesează Swagger UI la `http://127.0.0.1:8000/docs` pentru testare.

## Note
- Pentru căutare semantică, ChromaDB folosește doar embeddings generați cu OpenAI (nu procesează local cu ONNX).
- Poți extinde baza de date de cărți editând `data/summaries.json` și rulând din nou ingestia.
- Frontend-ul Next.js se află în folderul `frontend/`.

---

**Dezvoltat cu ajutorul GitHub Copilot**

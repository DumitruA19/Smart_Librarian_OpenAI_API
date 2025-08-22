# Smart Librarian

Smart Librarian is a full-stack AI-powered book recommendation platform. It features user authentication, a chat interface with conversation history, profanity filtering, favorites, and a dashboard. The backend uses FastAPI, SQL Server, and OpenAI; the frontend is built with React, Vite, and Tailwind CSS.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Installation & Setup](#installation--setup)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [Database Setup](#database-setup)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Customization & Extensions](#customization--extensions)
- [License](#license)
- [Contact](#contact)

---

## Project Overview

Smart Librarian helps users discover books through an intelligent chat assistant. It supports both Romanian and English, maintains chat history, filters inappropriate language, and allows users to save favorite books. The backend leverages OpenAI for recommendations and SQL Server for persistent storage. The frontend provides a modern, responsive UI.

---

## Features

- **User Authentication:** Register, login, logout, JWT-based session management.
- **AI Chat:** Book recommendations via OpenAI, with context-aware responses and multi-language support.
- **Profanity Filtering:** Customizable list in `backend/app/core/bad_words.txt`.
- **Dashboard:** Overview of user activity and recommendations.
- **RAG (Retrieval Augmented Generation):** ChromaDB integration for fast search and summarization.

---

## Architecture

- **Frontend:** React, Vite, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy, SQL Server, OpenAI API
- **Database:** SQL Server (users, chat history, favorites)
- **RAG:** ChromaDB (for advanced retrieval and summarization)
- **Profanity Filtering:** Text file-based, easily extendable
- **Authentication:** JWT, with protected routes and auto-refresh

---

## Folder Structure

```
Smart_Librarian/
│
├── backend/
│   ├── app/
│   │   ├── core/         # Config, OpenAI client, profanity filter, security
│   │   ├── models/       # SQLAlchemy models, Pydantic schemas
│   │   ├── rag/          # ChromaDB tools for RAG
│   │   ├── routers/      # FastAPI routers (auth, chat, etc)
│   │   ├── tools/        # Summaries and utility scripts
│   │   └── main.py       # FastAPI entry point
│   ├── chroma_store/     # ChromaDB storage
│   ├── data/             # Book summaries, JSON data
│   ├── requirements.txt
│   ├── .env
│   └── backend.md
│
├── frontend/
│   ├── src/
│   │   ├── api/          # API client, auth, chat
│   │   ├── app/          # Next.js/React pages
│   │   ├── auth/         # Context, ProtectedRoute
│   │   ├── components/   # Navbar, ChatMessage, MessageInput, etc
│   │   ├── pages/        # Chat, Login, Register
│   │   ├── store/        # Zustand store for chat
│   │   ├── assets/       # SVGs, images
│   │   └── index.css     # Tailwind CSS
│   ├── public/           # Static files, icons
│   ├── .env
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
│
├── sql/
│   └── 01_schema.sql     # SQL script for database schema
│
└── readme.md
```

---

## Installation & Setup

### Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (v3.10+ recommended)
- **SQL Server** (local or cloud instance)
- **OpenAI API Key** (get from https://platform.openai.com/)
- **ODBC Driver 17 for SQL Server** (for backend DB connection)

---

### Backend Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd Smart_Librarian/backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # On Windows
   # Or: source venv/bin/activate   # On Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Edit `backend/.env`:
   ```ini
   SQLSERVER_CONN_STR=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=Smart_librarian_users;UID=sa;PWD=your_password
   OPENAI_API_KEY=sk-xxx
   CHAT_MODEL=gpt-4.1-nano
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
   ```

5. **Run the backend server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   > Remove `--reload` for production.

---

### Frontend Setup

1. **Go to the frontend folder:**
   ```bash
   cd ../frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Configure environment variables:**
   Edit `frontend/.env`:
   ```ini
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```

4. **Run the frontend server:**
   ```bash
   npm run dev
   ```
   > Access the app at [http://localhost:5173](http://localhost:5173)

---

### Database Setup

1. **Install SQL Server locally or use a cloud instance (Azure SQL, AWS RDS, etc).**
2. **Install ODBC Driver 17 for SQL Server.**
3. **Create the database and tables:**
   - Open SQL Server Management Studio or Azure Data Studio.
   - Run the script in `sql/01_schema.sql` to create tables for users, chat history, favorites, etc.

---

## Usage

- **Register a new account** or log in with existing credentials.
- **Start a chat** and ask for book recommendations in Romanian or English.
- **View conversation history** and get context-aware answers.
- **Save favorite books** for later.
- **Test profanity filtering** by sending messages with words from `bad_words.txt`.
- **Access dashboard** for activity overview.

---

## Development

- **Hot reload:** Use `uvicorn app.main:app --reload` for backend and `npm run dev` for frontend.
- **Linting:** ESLint and Prettier are configured for frontend.
- **Styling:** Tailwind CSS for rapid UI development.
- **API calls:** All requests go through `src/api/client.js` with JWT attached.

---

## Testing

- **Manual testing:** Use the chat interface to send various questions (see below).
- **Sample questions:**
  - "Recomandă-mi o carte despre supraveghere și propagandă."
  - "Can you recommend a dystopian novel about freedom?"
  - "Ce carte fantasy pentru toate vârstele îmi sugerezi?"
  - "Suggest a book that explores friendship and courage."
- **Profanity filter:** Try sending messages with words from `bad_words.txt` to test blocking.

---

## Deployment

### Docker

You can containerize both backend and frontend:

- **Backend Dockerfile example:**
  ```dockerfile
  FROM python:3.10
  WORKDIR /app
  COPY . .
  RUN pip install -r requirements.txt
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- **Frontend Dockerfile example:**
  ```dockerfile
  FROM node:18
  WORKDIR /app
  COPY . .
  RUN npm install
  RUN npm run build
  EXPOSE 5173
  CMD ["npm", "run", "preview"]
  ```

- **docker-compose.yml example:**
  ```yaml
  version: '3'
  services:
    backend:
      build: ./backend
      ports:
        - "8000:8000"
      env_file:
        - ./backend/.env
    frontend:
      build: ./frontend
      ports:
        - "5173:5173"
      env_file:
        - ./frontend/.env
  ```

### Cloud

- **Backend:** Deploy to Azure Web Apps, AWS EC2, Google Cloud Run, or Heroku.
- **Frontend:** Deploy to Vercel, Netlify, Azure Static Web Apps, or AWS Amplify.
- **Database:** Use Azure SQL, AWS RDS, or Google Cloud SQL.

---

## Troubleshooting

- **CORS errors:** Check `CORS_ORIGINS` in backend `.env` and make sure frontend uses the correct port.
- **500 Internal Server Error:** Check SQL Server connection string and OpenAI API key.
- **422 Unprocessable Content:** Ensure frontend sends `{ history: [...] }` as payload to `/chat`.
- **Model hallucinations:** Use a larger model and optimize the system prompt in `openai_client.py`.
- **Database connection issues:** Verify SQL Server is running, credentials are correct, and ODBC driver is installed.

---

## Customization & Extensions

- **Add new bad words:** Edit `backend/app/core/bad_words.txt`.
- **Change system prompt:** Edit `chat_complete` in `openai_client.py`.
- **Add new pages/components:** Extend React components in `frontend/src/components` and `frontend/src/pages`.
- **Integrate other AI models:** Modify backend to use different APIs or local models.
- **Improve RAG:** Use `backend/app/rag/` for advanced retrieval and summarization.

---

## License

This project is open-source. See the repository for license details.

---

## Contact

For questions, issues, or contributions, open an issue on GitHub or contact

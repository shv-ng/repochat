# RepoChat

A full-stack application that lets you index any public GitHub repository and chat with its codebase using AI. Ask natural language questions and get answers grounded in the actual source code.

![RepoChat](https://img.shields.io/badge/stack-SvelteKit%20%2B%20Django-blue)

## Features

- **Repository Ingestion** — Clone and index any public GitHub repo into a vector store
- **Semantic + Keyword Search** — Hybrid retrieval using ChromaDB for accurate context
- **Streaming Chat** — Real-time streamed responses powered by Groq (Llama 3.3 70B)
- **Chat History** — Persistent conversation history per repo session
- **Authentication** — JWT-based user accounts with login/register
- **Previously Ingested Repos** — Quick access to repos you've already indexed

## Tech Stack

**Frontend**
- SvelteKit 5 with TypeScript
- Tailwind CSS + shadcn-svelte components
- `marked` for markdown rendering in chat

**Backend**
- Django 6 + Django REST Framework
- Celery + Redis for async ingestion tasks
- ChromaDB for vector storage
- LangChain + Groq (Llama 3.3 70B) for LLM streaming
- PostgreSQL for persistence
- JWT authentication via `djangorestframework-simplejwt`

## Architecture

```
User → SvelteKit Frontend
         ↓
   Django REST API
    ├── Ingestion (POST /api/ingest/)
    │     └── Celery Task → Clone repo → Chunk files → Embed into ChromaDB
    ├── Chat (GET /api/chat/)
    │     └── Hybrid search ChromaDB → Stream LLM response via SSE
    ├── Auth (/api/auth/register/, /api/auth/token/, /api/auth/refresh/)
    └── Repos (GET /api/repos/)
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A [Groq API key](https://console.groq.com)

### Running with Docker Compose

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd repochat
   ```

2. Create a `.env` file in the project root (or set environment variables):
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

3. Start all services:
   ```bash
   docker compose up --build
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Running Locally (without Docker)

**Backend**

```bash
cd backend
# Install dependencies (requires uv)
uv sync

# Set environment variables
export GROQ_API_KEY=your_key
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

# Run migrations
uv run python manage.py migrate

# Start Django
uv run python manage.py runserver

# Start Celery worker (separate terminal)
uv run celery -A config worker -l info
```

**Frontend**

```bash
cd frontend
cp .env.example .env   # set PUBLIC_BASE_URL=http://localhost:8000
npm install
npm run dev
```

## Usage

1. **Register / Login** using the button in the top-right corner (optional — anonymous use is supported for chat, but repo history requires an account).
2. **Paste a GitHub URL** (e.g. `https://github.com/owner/repo`) and click **Ingest Repository**.
3. Wait for indexing to complete — progress is shown in real time.
4. **Ask questions** about the codebase in the chat interface.
5. Previously ingested repos appear on the home screen for quick access.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Create a new account |
| POST | `/api/auth/token/` | Obtain JWT tokens |
| POST | `/api/auth/refresh/` | Refresh access token |
| POST | `/api/ingest/` | Start repo ingestion |
| GET | `/api/ingest/?job_id=<id>` | Stream ingestion status (SSE) |
| GET | `/api/chat/?repo_url=&query=&session_id=` | Stream chat response (SSE) |
| GET | `/api/chat/history/?session_id=<id>` | Fetch chat history |
| GET | `/api/repos/` | List user's ingested repos |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Required. Your Groq API key |
| `DB_NAME` | `postgres` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL for Celery |
| `PUBLIC_BASE_URL` | — | Frontend: backend base URL |

## Project Structure

```
repochat/
├── backend/
│   ├── apps/
│   │   ├── accounts/     # User registration & JWT auth
│   │   ├── chat/         # Chat sessions & message history
│   │   ├── ingestion/    # Ingestion jobs & SSE status
│   │   └── repos/        # Repo registry
│   ├── services/
│   │   ├── github/       # Git clone & file parsing/chunking
│   │   ├── llm/          # LangChain + Groq streaming
│   │   └── vectorstore/  # ChromaDB embed & search
│   ├── tasks/
│   │   └── ingest.py     # Celery ingestion task
│   └── config/           # Django settings, URLs, Celery
└── frontend/
    └── src/
        ├── routes/       # SvelteKit pages (+page.svelte, chat/)
        └── lib/          # API client, stores, UI components
```

## Notes

- Only **public** GitHub repositories are supported.
- Large repositories may take a minute or two to index.
- The LLM is instructed to answer strictly from the indexed code context and will say so if an answer isn't found.
- File types with language-aware chunking: Python, Go, Java, Rust, C#, Ruby, Kotlin, PHP, Scala, Swift, and more. JSON, Markdown, and HTML have dedicated splitters.

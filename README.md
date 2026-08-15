# StackRAG Backend

FastAPI backend for a document question-answering application built around financial PDFs.

This repository contains the API, document-ingestion pipeline, storage layer, retrieval workflow, and model-provider integrations. The UI lives in [StackRAG-Frontend](https://github.com/BryanTheLai/StackRAG-Frontend).

## Scope

The current codebase includes:

- PDF upload and background processing
- metadata extraction, sectioning, chunking, and embeddings
- Supabase Auth, Storage, Postgres, and pgvector integration
- user-scoped vector retrieval
- a chat endpoint that streams server-sent events
- a Python calculation tool for numeric questions
- evaluation scripts and a sample dataset under `evaluation/`

The evaluation files are tied to their dataset, model configuration, and test run. They are useful for comparing changes; they are not general accuracy or uptime guarantees.

## Architecture

```mermaid
flowchart LR
    Client[Web client or API client] --> API[FastAPI]
    API --> Auth[Supabase Auth]
    API --> Storage[Supabase Storage]
    API --> DB[(Postgres + pgvector)]
    API --> Models[OpenAI or Gemini]
    API --> Pipeline[Document pipeline]
    Pipeline --> Storage
    Pipeline --> DB
```

### Document flow

1. An authenticated client uploads a PDF.
2. The API creates a processing job and runs the ingestion pipeline in the background.
3. The pipeline parses the file, extracts metadata, creates sections and chunks, and stores embeddings.
4. The client can read processing status and the resulting document records.

### Chat flow

1. The client sends conversation history to `POST /api/v1/chat/stream`.
2. The backend retrieves chunks for the authenticated user.
3. The RAG workflow can call retrieval and calculation tools while composing the response.
4. Response chunks are returned as server-sent events.

## API

All endpoints below the `/api` prefix require a Supabase access token in `Authorization: Bearer <token>`. The health endpoint does not require authentication.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Return service status |
| `POST` | `/api/v1/documents/process` | Upload and process a PDF |
| `GET` | `/api/v1/documents` | List the current user's documents |
| `GET` | `/api/v1/documents/{id}` | Read a document record |
| `POST` | `/api/v1/chat/stream` | Stream a RAG response as SSE |

Interactive API documentation is available at `http://localhost:8000/docs` when the server is running.

Example upload:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/process" \
  -H "Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN" \
  -F "file=@financial_report.pdf"
```

Example chat request:

```bash
curl -N -X POST "http://localhost:8000/api/v1/chat/stream" \
  -H "Authorization: Bearer YOUR_SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"history": [{"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "What was the revenue growth?"}]}]}'
```

## Local setup

### Requirements

- Python 3.12 or newer
- A Supabase project
- An OpenAI or Gemini API key
- Docker and Docker Compose, if using the container setup

### Python

```bash
git clone https://github.com/BryanTheLai/StackRAG-Backend.git
cd StackRAG-Backend
python -m venv .venv
```

Activate the environment, then install dependencies:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

Create `.env` from `.env.example` and set the values required by your chosen provider and Supabase project:

```env
GEMINI_API_KEY=
OPENAI_API_KEY=
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
```

Start the API from the repository root:

```bash
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
```

### Database setup

Run the SQL files in `scripts/` in numeric order in the Supabase SQL editor. They create the tables, vector search function, storage policies, and processing-job tracking used by the application.

The scripts contain development-oriented reset statements such as `DROP TABLE`. Review them before running them against an existing database.

### Docker Compose

```bash
docker compose up --build
```

The compose file exposes the API on port `8000` and loads variables from `.env`.

## Repository layout

```text
api/
  v1/endpoints/       FastAPI route handlers
src/
  llm/                Model clients, tools, and RAG workflow
  services/           Parsing, metadata, sectioning, chunking, embeddings
  storage/            Supabase persistence
  prompts/            Jinja prompt templates
  models/             Pydantic models
  pipeline.py         Ingestion orchestration
evaluation/            Evaluation scripts and sample data
scripts/               Database setup SQL
Dockerfile             Container setup for local use
Dockerfile.prod        Alternate multi-stage container build
docker-compose.yml     Local container orchestration
```

## Configuration notes

- `CHAT_PROVIDER` selects the chat provider; the workflow defaults to Gemini.
- `GEMINI_CHAT_MODEL` and `OPENAI_CHAT_MODEL` override provider model names.
- `MAX_CONCURRENT_INGESTIONS` limits concurrent document jobs.
- `DOCUMENT_PROCESS_MAX_ATTEMPTS` controls retry attempts for transient model errors.
- Keep `.env` out of version control. Client-side applications should use only the Supabase public/anon key, never a service-role key.

## License

MIT. See [LICENSE](LICENSE).

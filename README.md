# Daleel KU

An AI-powered, bilingual academic chatbot for Kuwait University students. Built as an ISC 499 Capstone project (Spring 2025/2026).

Students ask questions in Arabic or English and get answers sourced directly from the KU knowledge base. Students select their preferred interface language via a toggle. The chatbot automatically detects the language of each query and responds in the same language. A separate admin panel lets authorized KU staff manage the knowledge base and review query logs.

---

## Tech Stack

**Backend**: Flask · LlamaIndex · GPT-4o · Supabase (pgvector) · Flask-Limiter  
**Frontend**: React · TypeScript · Tailwind CSS · Vite  
**AI**: OpenAI GPT-4o for generation and query classification, LlamaIndex for RAG pipeline management

---

## Project Structure

```
daleel-ku/
├── backend/
│   ├── app.py              # Flask application
│   ├── config.py           # Shared state: supabase, llm, embed_model
│   ├── routes/
│   │   ├── chat.py         # POST /api/query, POST /api/session
│   │   └── admin.py        # Admin CRUD routes
│   ├── auth/
│   │   └── jwt.py          # JWT verify/issue for admin auth
│   ├── rag/
│   │   ├── ingest.py       # Document ingestion → VectorStoreIndex
│   │   ├── query_engine.py # pgvector similarity search
│   │   └── response.py     # Bilingual GPT-4o response generation
│   └── ingestion/
│       ├── pdf.py          # LlamaParse PDF extraction (vision-based)
│       ├── scraper.py      # Firecrawl web crawling
│       └── social.py       # Apify social media scraping
└── frontend/
    └── src/
        ├── pages/          # Index, Landing, NotFound, admin/*
        └── components/     # Chat UI, admin panel components
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js
- Supabase project with pgvector enabled
- OpenAI API key
- Llama Cloud API key (for LlamaParse PDF extraction)
- Firecrawl API key (for web crawling)
- Apify API key (for social media scraping)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

cp .env.example .env         # then fill in your credentials
python app.py                # Flask runs on http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install                  # or: bun install
npm run dev                  # Vite dev server on http://localhost:5173
```

---

## Environment Variables

Create `backend/.env` from the example file. Variables marked **required** will raise an error on startup if missing.

| Variable               | Default                 | Where to get it                                                                   |
| ---------------------- | ----------------------- | --------------------------------------------------------------------------------- |
| `OPENAI_API_KEY`       | **required**            | platform.openai.com                                                               |
| `SUPABASE_URL`         | **required**            | Supabase dashboard → Settings → API                                               |
| `SUPABASE_KEY`         | **required**            | Supabase dashboard → Settings → API (use the legacy anon key starting with `eyJ`) |
| `SUPABASE_SERVICE_KEY` | **required**            | Supabase dashboard → Settings → API (service role key)                            |
| `LLAMA_CLOUD_API_KEY`  | **required**            | cloud.llamaindex.ai → API Keys (free tier available)                              |
| `FIRECRAWL_API_KEY`    | optional                | firecrawl.dev → Dashboard → API Keys                                              |
| `APIFY_API_KEY`        | optional                | apify.com → Settings → Integrations                                               |
| `JWT_ALGORITHM`        | `HS256`                 | —                                                                                 |
| `JWT_EXPIRY_HOURS`     | `8`                     | —                                                                                 |
| `FLASK_DEBUG`          | `false`                 | —                                                                                 |
| `FRONTEND_URL`         | `http://localhost:5173` | —                                                                                 |

---

## How It Works

When a student submits a question:

1. The query is validated (1000 char max, non-empty)
2. GPT-4o classifies it as `"gpa"` or `"general"`
3. **GPA queries** go directly to the LLM with a hardcoded KU grade scale prompt — no retrieval needed
4. **General queries** go through the RAG pipeline: embed → pgvector search → top-5 chunks → GPT-4o response
5. The query and response are logged anonymously to the `user_query` table
6. The response is returned with a `was_answered` flag (if `false`, the student is redirected to the relevant KU department)

The pipeline supports bilingual input. Arabic and English queries are both supported, and responses mirror the input language.

---

## Admin Panel

Accessible to authorized KU staff only. JWT-based auth (tokens expire after 8 hours).

| Page               | Purpose                                                         |
| ------------------ | --------------------------------------------------------------- |
| Login              | Credential form, JWT issued on success                          |
| Dashboard          | Query stats, recent activity                                    |
| Content Management | Add, edit, delete documents in the knowledge base               |
| Query Logs         | Browse queries grouped by session, filter by status, export CSV |

---

## API Endpoints

### Student (public)

**`POST /api/session`**  
Creates a new chat session. Call this once when the student opens the chat page and attach the returned `session_id` to all subsequent query requests.

| Field        | Details                    |
| ------------ | -------------------------- |
| Request body | _(none)_                   |
| `201`        | `{ "session_id": string }` |
| `500`        | `{ "error": string }`      |

**`PATCH /api/session/<session_id>`**  
Closes an open session by recording its end time. Call this before starting a new session.

| Field        | Details                                     |
| ------------ | ------------------------------------------- |
| URL param    | `session_id` — UUID of the session to close |
| Request body | _(none)_                                    |
| `200`        | `{ "session_id": string }`                  |
| `500`        | `{ "error": string }`                       |

**`POST /api/query`** — rate limited to 30 req/min per IP  
Submits a student question and returns the chatbot's response.

| Field        | Details                                                                   |
| ------------ | ------------------------------------------------------------------------- |
| `message`    | string, required — the student's question (max 1000 chars)                |
| `session_id` | string, optional — UUID from `POST /api/session`                          |
| `200`        | `{ "response": string, "source": string\|null, "was_answered": boolean }` |
| `400`        | `{ "error": string }` — empty query or exceeds 1000 chars                 |
| `429`        | `{ "error": string }` — rate limit exceeded                               |
| `500`        | `{ "error": string }`                                                     |

---

### Admin (protected — requires `Authorization: Bearer <token>`)

**`POST /api/admin/login`**  
Authenticates an admin user via Supabase Auth and returns a JWT access token.

| Field      | Details                                          |
| ---------- | ------------------------------------------------ |
| `email`    | string, required                                 |
| `password` | string, required                                 |
| `200`      | `{ "access_token": string }`                     |
| `400`      | `{ "error": "email and password are required" }` |
| `401`      | `{ "error": "Invalid credentials" }`             |

**`GET /api/admin/documents`**  
Returns all documents in the knowledge base.

| Field        | Details                              |
| ------------ | ------------------------------------ |
| Request body | _(none)_                             |
| `200`        | `{ "documents": [ document, ... ] }` |
| `500`        | `{ "error": string }`                |

**`POST /api/admin/documents`**  
Adds a new document record to the knowledge base.

| Field           | Details                                        |
| --------------- | ---------------------------------------------- |
| `title`         | string, required                               |
| `source_url`    | string                                         |
| `document_type` | string                                         |
| `admin_id`      | string — UUID of the admin adding the document |
| `201`           | `{ "document": object }`                       |
| `400`           | `{ "error": "Request body is required" }`      |
| `500`           | `{ "error": string }`                          |

**`PUT /api/admin/documents/<doc_id>`**  
Updates an existing document by ID.

| Field        | Details                                   |
| ------------ | ----------------------------------------- |
| URL param    | `doc_id` — UUID of the document to update |
| Request body | any subset of document fields to update   |
| `200`        | `{ "document": object }`                  |
| `400`        | `{ "error": "Request body is required" }` |
| `500`        | `{ "error": string }`                     |

**`DELETE /api/admin/documents/<doc_id>`**  
Deletes a document by ID.

| Field        | Details                                   |
| ------------ | ----------------------------------------- |
| URL param    | `doc_id` — UUID of the document to delete |
| Request body | _(none)_                                  |
| `200`        | `{ "message": "Document deleted" }`       |
| `500`        | `{ "error": string }`                     |

**`GET /api/admin/queries`**  
Returns all logged student queries, ordered newest first.

| Field        | Details                         |
| ------------ | ------------------------------- |
| Request body | _(none)_                        |
| `200`        | `{ "queries": [ query, ... ] }` |
| `500`        | `{ "error": string }`           |

---

## Database

8 tables in Supabase with the pgvector extension enabled.

| Table        | Purpose                                                                        |
| ------------ | ------------------------------------------------------------------------------ |
| `session`    | Tracks each anonymous student chat session (`started_at`, `ended_at`)          |
| `user_query` | Logs every query and response — no PII, analytics only                         |
| `admin_user` | Stores admin credentials (`email`, `password_hash`)                            |
| `document`   | Metadata for each ingested document (`title`, `source_url`, `document_type`)   |
| `chunk`      | The central entity — a piece of text from a document with its vector embedding |
| `topic`      | Lookup table for content topics                                                |
| `source`     | Lookup table for content sources (`source_name`, `url`)                        |
| `college`    | Lookup table for KU colleges                                                   |

**Relationships**

- `session` → `user_query` (1:N) — queries are optionally linked to a session
- `admin_user` → `document` (1:N) — tracks which admin added a document
- `document` → `chunk` (1:N) — a document is split into multiple chunks at ingestion
- `chunk` → `topic`, `source`, `college` (N:1 each) — each chunk is tagged with metadata for filtering

---

## Security

- **Rate limiting**: 30 requests/min on `POST /api/query` only
- **JWT auth**: all admin routes require a valid Supabase-issued JWT (verified via Supabase Auth)
- **Input validation**: query length capped at 1000 chars; system prompt and user input are always kept structurally separate in the OpenAI API call
- **CORS**: restricted to `FRONTEND_URL`
- **No Personal Information stored**: GPA inputs are session-only and never persisted

---

## Knowledge Base Scope

- **University-wide**: general information relevant to all KU students
- **CLS-specific**: detailed academic guidance for College of Life Sciences students

Content is ingested from PDFs (via LlamaParse), web pages (via Firecrawl), and social media (via Apify + GPT-4o Vision for OCR).

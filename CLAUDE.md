# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Daleel KU is an AI-powered, bilingual (Arabic + English) academic chatbot for Kuwait University students — ISC 499 Capstone (Spring 2025/2026). Students submit questions; the backend uses a RAG pipeline (LlamaIndex + GPT-4o + Supabase pgvector) to retrieve chunks from the KU knowledge base and generate bilingual responses. A separate admin panel lets authorized KU staff manage the knowledge base and review query logs. No student authentication — sessions are anonymous.

## Running the Backend

```bash
# From backend/
venv\Scripts\activate          # Must activate before anything else (Windows)
python app.py                  # Flask on port 5000
```

Flask uses the application factory pattern (`create_app()` in `app.py`). Blueprints **must** be imported inside `create_app()`, not at the top of the file — `routes/chat.py` does `from app import limiter`, so `limiter` must already exist when that import runs.

## Environment Variables

Copy `backend/.env.example` to `backend/.env`. Variables that raise `ValueError` on startup if missing:

| Variable | Notes |
|---|---|
| `OPENAI_API_KEY` | Required |
| `SUPABASE_URL` | Required |
| `SUPABASE_KEY` | Use legacy anon key (starts with `eyJ`, not `sb_publishable`) |
| `SUPABASE_JWT_SECRET` | From Supabase dashboard → Settings → API → JWT Settings |

Optional / currently commented out in `config.py`:
- `FIRECRAWL_API_KEY` — uncomment when Firecrawl integration is ready
- `APIFY_API_KEY` — uncomment when Apify integration is ready

Other: `JWT_ALGORITHM=HS256`, `JWT_EXPIRY_HOURS=8`, `FLASK_DEBUG=true`, `FRONTEND_URL=http://localhost:5173`

## Architecture

The system is organized into six packages (from Report III package diagram):

```
backend/
├── app.py              # Flask factory — CORS, rate limiter, blueprint registration
├── config.py           # Shared state: supabase client, llm (gpt-4o), embed_model, env vars
├── routes/
│   ├── chat.py         # POST /api/query (30/min rate limit), POST /api/session
│   └── admin.py        # Admin CRUD routes — currently empty
├── auth/
│   └── jwt.py          # JWT verify/issue for admin — currently empty
├── rag/
│   ├── ingest.py       # build_index(): SimpleDirectoryReader → SentenceSplitter(512/50) → VectorStoreIndex
│   ├── query_engine.py # search_and_build_context(): similarity_top_k=3 → context string
│   └── response.py     # generate_response(): bilingual system prompt → GPT-4o → {answer, was_answered}
└── ingestion/
    ├── pdf.py          # PyMuPDF text + image extraction — empty
    ├── scraper.py      # Firecrawl web crawling — empty
    └── social.py       # Apify social media scraping — empty

frontend/               # React + TypeScript + Tailwind + shadcn/ui — currently empty
                        # Code to be copied from Lovable
```

**Central config rule:** `llm`, `embed_model`, and `supabase` are initialized once in `config.py`. Never reinitialize them elsewhere — import from `config`.

## Data Flow (UC02 — Student Query)

1. React `POST /api/query` → Flask validates input (1000 char max, no empty)
2. `detect_query_type()` calls GPT-4o to classify as `"gpa"` or `"general"` (max_tokens=5, temp=0)
3. **GPA queries** → directly to LLM with hardcoded KU grade scale prompt (no RAG)
4. **General queries** → RAG pipeline: embed query → pgvector search → top-3 chunks → GPT-4o response
5. Log to `user_query` table (query text, response, `was_answered`, timestamp — no PII)
6. Return `{response, source, was_answered}`

The RAG routing in `chat.py` is currently commented out (stub response until `rag/` is implemented).

## Database (Supabase + pgvector)

8 tables: `session`, `user_query`, `admin_user`, `document`, `chunk`, `source`, `topic`, `college`

- `chunk.embedding` is `VECTOR(1536)` — requires pgvector extension (already enabled)
- `chunk` is the central entity: belongs to `document`, `source`, `topic`, and `college`
- `session` → `user_query` (1:N); `admin_user` → `document` (1:N); `document` → `chunk` (1:N)
- `user_query` is standalone (analytics only, no FK to session required but optional)
- `was_answered = false` flags unanswered queries so admins can identify knowledge gaps

## Security Design (from Report III)

- **Admin auth**: Supabase Auth issues JWTs; Flask backend verifies on every request using `SUPABASE_JWT_SECRET`. Tokens expire after `JWT_EXPIRY_HOURS` (8h).
- **Rate limiting**: Flask-Limiter at 30 req/min on `POST /api/query` only — not on admin routes.
- **Input validation**: 1000-char max + non-empty check before any processing. Prevents prompt injection by keeping system prompt and user input structurally separate in the OpenAI API call.
- **SQL injection**: mitigated by Supabase client's parameterized queries.
- **No PII**: query logs store only text + timestamp. GPA inputs are session-only, never persisted.
- **CORS**: restricted to `FRONTEND_URL` from `.env`.

## What Still Needs to Be Built

**High priority (needed for working demo):**
- `auth/jwt.py` — JWT verify/issue functions for admin routes
- `routes/admin.py` — admin login, document CRUD, query log endpoints
- Uncomment RAG routing block in `routes/chat.py` once `rag/` files are implemented
- Connect React frontend: update `Index.tsx` to call real Flask instead of fake `setTimeout`

**Lower priority:**
- `ingestion/pdf.py` — PyMuPDF text and image extraction
- `ingestion/scraper.py` — Firecrawl web crawling
- `ingestion/social.py` — Apify Instagram/social scraping
- GPA flow: multi-turn conversation to collect course grades, credit hours, cumulative GPA

## Key Technical Constraints

- `openai` v2.30.0 (not v1.x — API structure differs)
- `llama-index` v0.14.19
- `supabase` v2.28.3
- `data/` folder: `SimpleDirectoryReader` reads all files automatically (`.txt` and `.pdf`)
- Language mirroring: chatbot detects input language (Arabic/English) and responds in the same language
- Frontend is RTL for Arabic — `shadcn/ui` components must support RTL rendering
- GPT-4o Vision for OCR on images from social media (base64 input, not URLs; extracted text only — no images stored)
- Knowledge base scope: university-wide general info for all KU students; detailed CLS-specific academic guidance for College of Life Sciences students only

## Admin Panel Pages (from Report III UI design)

1. **Login** — credential form, JWT issued on success
2. **Dashboard** — cards (Total Documents, Total Queries, Answered, Referral), recent queries table, latest content
3. **Content Management** — document table (title, type, college, topic, date, source URL), add/edit/delete, search
4. **Query Logs** — grouped by session, filter by All/Answered/Referral, export CSV

"Referral" = `was_answered = false`, student was redirected to official KU department.

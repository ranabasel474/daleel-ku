# Daleel KU — دليل جامعة الكويت

An AI-powered, bilingual academic chatbot for Kuwait University students. Built as an ISC 499 Capstone project (Spring 2025/2026).

Students ask questions in Arabic or English and get answers sourced directly from the KU knowledge base. The chatbot mirrors the user's language automatically. A separate admin panel lets authorized KU staff manage the knowledge base and review query logs.

---

## Tech Stack

**Backend** — Flask · LlamaIndex · GPT-4o · Supabase (pgvector) · Flask-Limiter  
**Frontend** — React · TypeScript · Tailwind CSS · Vite  
**Database** — Supabase + pgvector (1536-dim embeddings)  
**AI** — OpenAI GPT-4o for generation and query classification, LlamaIndex for RAG orchestration

---

## Project Structure

```
daleel-ku/
├── backend/
│   ├── app.py              # Flask application factory
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
│       ├── pdf.py          # PyMuPDF text + image extraction
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
- Node.js 18+ (or Bun)
- A Supabase project with pgvector enabled
- An OpenAI API key

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

Create `backend/.env` from the example file. The following are required — the app will raise an error on startup if any are missing:

| Variable | Where to get it |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com |
| `SUPABASE_URL` | Supabase dashboard → Settings → API |
| `SUPABASE_KEY` | Use the legacy anon key (starts with `eyJ`) |
| `SUPABASE_JWT_SECRET` | Supabase dashboard → Settings → API → JWT Settings |

Optional variables (for integrations not yet active):

```
FIRECRAWL_API_KEY=
APIFY_API_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8
FLASK_DEBUG=true
FRONTEND_URL=http://localhost:5173
```

---

## How It Works

When a student submits a question:

1. The query is validated (1000 char max, non-empty)
2. GPT-4o classifies it as `"gpa"` or `"general"`
3. **GPA queries** go directly to the LLM with a hardcoded KU grade scale prompt — no retrieval needed
4. **General queries** go through the RAG pipeline: embed → pgvector search → top-3 chunks → GPT-4o response
5. The query and response are logged to the `user_query` table (no PII stored)
6. The response is returned along with a `was_answered` flag

Unanswered queries (`was_answered = false`) are surfaced in the admin panel so staff can identify knowledge gaps.

---

## Admin Panel

Accessible to authorized KU staff only. JWT-based auth (tokens expire after 8 hours).

| Page | Purpose |
|---|---|
| Login | Credential form, JWT issued on success |
| Dashboard | Query stats, recent activity |
| Content Management | Add, edit, delete documents in the knowledge base |
| Query Logs | Browse queries grouped by session, filter by status, export CSV |

---

## Database

8 tables in Supabase. The `chunk` table is the central entity — every retrieved piece of knowledge is a chunk tied to a document, source, topic, and college.

Key design choices:
- `chunk.embedding` is `VECTOR(1536)` — requires the pgvector extension (already enabled on the project)
- `user_query` stores only query text, response, and timestamp — no user identifiers
- `was_answered = false` marks referral cases (student redirected to a KU department)

---

## Security

- **Rate limiting**: 30 requests/min on `POST /api/query` only
- **JWT auth**: all admin routes require a valid Supabase-issued JWT verified against `SUPABASE_JWT_SECRET`
- **Input validation**: query length capped at 1000 chars; system prompt and user input are always kept structurally separate in the OpenAI API call
- **CORS**: restricted to `FRONTEND_URL`
- **No PII**: GPA inputs are session-only and never persisted

---

## Knowledge Base Scope

- **University-wide**: general information relevant to all KU students
- **CLS-specific**: detailed academic guidance for College of Life Sciences students

Content is ingested from PDFs, web pages (via Firecrawl), and social media (via Apify + GPT-4o Vision for OCR).

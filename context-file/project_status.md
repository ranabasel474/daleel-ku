# Daleel KU — Project Status

# Last Updated: April 4, 2026

================================================================================
CURRENT STATUS SUMMARY
================================================================================
<<<<<<< HEAD

=======
Deadline: April 9, 2026
>>>>>>> f1b582930a29cd106c76ecb218303b60452cc128
================================================================================
WHAT IS DONE
================================================================================

INFRASTRUCTURE:

- GitHub repo created: daleel-ku (private)
- Supabase project created: Daleel KU
- pgvector extension enabled in Supabase
- All 8 database tables created and verified:
  session, user_query, admin_user, document, chunk,
  source, topic, college
- Virtual environment created on both computers
- All packages installed on both computers

PACKAGES INSTALLED (requirements.txt):

- flask
- flask-cors
- flask-limiter
- python-dotenv
- supabase
- llama-index (0.14.19)
- llama-index-vector-stores-supabase
- openai (2.30.0)
- pymupdf
- firecrawl-py
- apify-client
- bcrypt

BACKEND FILES WRITTEN AND REVIEWED:

app.py — COMPLETE

- Flask app factory pattern (create_app())
- CORS configured with FRONTEND_URL from .env
- Rate limiter at module level (limiter.init_app)
- No global rate limit — applied per route in chat.py
- Blueprints registered: chat_bp at /api, admin_bp at /api/admin
- Health check at GET /
- Error handlers: 404, 429, 500 all return JSON
- debug mode from FLASK_DEBUG env variable
- import os included

config.py — COMPLETE

- load_dotenv() called first
- OPENAI_API_KEY — raises ValueError if not set
- SUPABASE_JWT_SECRET — raises ValueError if not set
  (renamed from JWT_SECRET to match Supabase Auth)
- JWT_ALGORITHM = HS256
- JWT_EXPIRY_HOURS = 8
- SUPABASE_URL + SUPABASE_KEY validated before create_client
- supabase client initialized
- llm = OpenAI(model="gpt-4o")
- embed_model = OpenAIEmbedding(model="text-embedding-3-small")
- Settings.llm and Settings.embed_model set globally
- FIRECRAWL_API_KEY — commented out (uncomment when ready)
- APIFY_API_KEY — commented out (uncomment when ready)

routes/chat.py — COMPLETE

- chat_bp Blueprint
- POST /query route with @limiter.limit("30 per minute")
- Input validation (InputValidator logic)
- Query type detection (QueryProcessor logic — GPA vs general)
- Calls RAG pipeline
- Logs to Supabase user_query table
- Returns JSON response
- POST /session route — creates session in Supabase

rag/ingest.py — COMPLETE

- build_index() function
- Loads all files from data/ using SimpleDirectoryReader
- Chunks with SentenceSplitter(chunk_size=512, chunk_overlap=50)
- Returns VectorStoreIndex
- Imports llm and embed_model from config.py

rag/query_engine.py — COMPLETE

- search_query(index, question) function
- similarity_top_k=3
- Returns top 3 relevant chunks as single context string
- Imports from config.py

rag/response.py — COMPLETE

- generate_response(context, query) function
- Bilingual system prompt (Arabic + English)
- Calls GPT-4o via llm.chat() from config.py
- Returns {"answer": str, "was_answered": bool}
- Fallback message in Arabic and English if context empty

FRONTEND:

- Fully built on Lovable (React + TypeScript + Tailwind + shadcn/ui)
- Pages: Landing, Chat UI (RTL Arabic), Admin Login,
  Admin Dashboard, Query Logs, Knowledge Base CRUD
- Plan: copy code from Lovable to frontend/ folder in repo
- frontend/ folder created in repo but empty

DATA:

- backend/data/ folder created
- StudentGuide25-26.pdf added (official KU student handbook)
- ku_info.txt created (needs more content)

================================================================================
FILE STRUCTURE
================================================================================

backend/
├── app.py ✅ complete
├── config.py ✅ complete
├── routes/
│ ├── **init**.py ✅ placeholder
│ ├── chat.py ✅ complete
│ └── admin.py ❌ empty
├── auth/
│ ├── **init**.py ✅ placeholder
│ └── jwt.py ❌ empty
├── rag/
│ ├── **init**.py ✅ placeholder
│ ├── ingest.py ✅ complete
│ ├── query_engine.py ✅ complete
│ └── response.py ✅ complete
├── ingestion/
│ ├── **init**.py ✅ placeholder
│ ├── scraper.py ❌ empty
│ ├── pdf.py ❌ empty
│ └── social.py ❌ empty
├── data/
│ ├── ku_info.txt ⚠️ created, needs content
│ └── StudentGuide25-26.pdf ✅ added
├── requirements.txt ✅ complete
├── .env ✅ on each computer, not on GitHub
└── .env.example ✅ committed to GitHub

frontend/
└── (empty — Lovable code to be copied here)

================================================================================
.ENV VARIABLES NEEDED
================================================================================

OPENAI_API_KEY= ← not set yet — Mahnoor getting this today
SUPABASE_URL= ← set
SUPABASE_KEY= ← set (legacy anon key, starts with eyJ)
SUPABASE_JWT_SECRET= ← get from Supabase Settings → API → JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=8
FLASK_DEBUG=true
FRONTEND_URL=http://localhost:5173

# Commented out until API keys are ready:

# FIRECRAWL_API_KEY=

# APIFY_API_KEY=

================================================================================
WHAT IS NOT DONE YET
================================================================================

HIGH PRIORITY (needed for working demo):

- OpenAI API key — Mahnoor getting today
- auth/jwt.py — needed for admin routes
- routes/admin.py — admin panel backend
- Connect frontend to backend (small change in Index.tsx)
- First end-to-end test run
- ku_info.txt content — needs real KU data

LOW PRIORITY (document as future work if not done):

- ingestion/scraper.py — Firecrawl web scraping
- ingestion/pdf.py — PyMuPDF extraction
- ingestion/social.py — Apify social media
- GPA estimation feature
- Source citations in responses

================================================================================
IMPORTANT TECHNICAL NOTES
================================================================================

- openai package is version 2.30.0 (NOT 1.x — API is different)
- llama-index version is 0.14.19
- supabase version is 2.28.3
- Use legacy anon key from Supabase (starts with eyJ, not sb_publishable)
- SUPABASE_JWT_SECRET comes from Supabase dashboard:
  Settings → API → JWT Settings → JWT Secret
- Rate limiting: 30 per minute on /api/query only
- All RAG models initialized in config.py — never reinitialize elsewhere
- data/ folder: SimpleDirectoryReader reads ALL files automatically
  (both .txt and .pdf supported)
- venv must be activated before running: venv\Scripts\activate
- Server runs on port 5000: python app.py

================================================================================
NEXT STEPS IN ORDER
================================================================================

1. Get OpenAI API key and add to .env (Mahnoor — today)
2. Get SUPABASE_JWT_SECRET from Supabase dashboard and add to .env
3. Write auth/jwt.py via Claude Code
4. Write routes/admin.py via Claude Code
5. Run first test: python app.py
6. Test /api/query with a real Arabic question
7. Copy Lovable frontend code to frontend/ folder
8. Update Index.tsx to call real Flask instead of fake setTimeout
9. Full end-to-end test: React → Flask → RAG → response in chat UI
10. Write Report IV + appendix (specifications table + Gantt chart)

================================================================================
PROFESSOR'S ADDITIONAL REQUIREMENT (April 4)
================================================================================

Professor requested appendix for Report IV containing:

1. Table of all promised specifications from Reports I, II, III
   with implementation status (done / in progress / not started)
2. Updated Gantt chart showing planned vs actual dates

This will be prepared after the working demo is complete.

================================================================================
KEY DECISIONS MADE
================================================================================

1. LlamaIndex Python over TypeScript (Arabic support)
2. Apify over direct scraping (handles Instagram anti-bot)
3. GPT-4o Vision for OCR (base64 input required, not URLs)
4. No image storage — only extracted text saved
5. Flask for Python RAG logic (separate from Supabase Edge Functions)
6. Supabase for both relational data AND vector embeddings (pgvector)
7. Anonymous sessions — no student authentication needed
8. was_answered flag to track knowledge gaps for admin review
9. Iterative SDLC with 4 iterations
10. Focus on College of Life Sciences first (expandable later)
11. All GPA rules hardcoded in LLM prompt (no separate calculator)
12. File structure mirrors Report III class diagram exactly
13. Frontend moved from Lovable to own repo (plain React — no Lovable branding)
14. JWT_EXPIRY_HOURS set to 8 (matches university work day)
15. Rate limiting on chat endpoint only — not admin routes
16. FIRECRAWL and APIFY keys commented out until APIs are set up

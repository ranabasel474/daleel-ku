# Daleel KU — Diagrams Description for Claude Code

## Package Diagram — System Boundary

### Frontend Package
- ChatInterface: sendQuery(), displayResponse()
- AdminPanel: loadDashboard(), manageContent()
- APIService: postQuery()

### Backend Package
- ChatController: receiveQuery(), sendResponse()
- AdminController: manageContent(), viewQueryLogs()
- Auth: authenticate(), invalidateToken()
- QueryProcessor: detectQueryType(), routeQuery()
- InputValidator: validateQuery(), validateCredentials(), validateContentUpdate()

### RAG Pipeline Package
- IngestionPipeline: ingestSource(), generateEmbedding()
- QueryEngine: searchQuery(), buildContext()
- ResponseGenerator: generateResponse(), appendSourceReference(), handleFallback()

### Data Ingestion Package
- WebScraper: scrape(), crawl()
- PDFExtractor: extractText(), extractImages()
- SocialMediaScraper: fetchPosts(), extractImageText()
- Scheduler: schedule(), triggerIngestion()

### Database Package
- AdminUser, Document, Chunk, Source, Topic, College, Session, UserQuery

### External Services
- Firecrawl API: crawlWebsite(), extractContent()
- Apify API: scrapeSocialMedia()
- OpenAI API: generateResponse(), embedText(), visionExtract()

---

## Class Diagram — Key Attributes and Methods

### Backend

**ChatController**
- sessionID: int
- receiveQuery(text: String): void
- sendResponse(s: String): void

**AdminController**
- adminID: int
- manageContent(): void
- viewQueryLogs(): void

**Auth**
- sessionToken: String
- expiresAt: DateTime
- authenticate(username: String, pass_hash: String): Boolean
- invalidateToken(): void

**QueryProcessor**
- queryType: String
- language: String
- detectQueryType(text: String): String
- routeQuery(type: String): void

**InputValidator**
- maxLength: int
- allowedChars: String
- validateQuery(input: String): Boolean
- validateCredentials(u: String, p: String): Boolean
- validateContentUpdate(data: String): Boolean

### RAG Pipeline

**QueryEngine**
- topK: int
- similarityThreshold: Float
- searchQuery(text: String): List
- buildContext(chunks: List): String

**IngestionPipeline**
- chunkSize: int
- language: String
- ingestSource(source: String): void
- generateEmbedding(chunk: String): Vector

**ResponseGenerator**
- systemPrompt: String
- language: String
- generateResponse(context: String, query: String): String
- appendSourceReference(response: String): String
- handleFallback(): String

### Data Ingestion

**WebScraper**
- targetURL: String
- lastScraped: DateTime
- scrape(url: String): String
- crawl(rootURL: String): List

**PDFExtractor**
- filePath: String
- language: String
- extractText(file: File): String
- extractImages(file: File): List

**SocialMediaScraper**
- platform: String
- accountIDs: List
- fetchPosts(handle: String): List
- extractImageText(img: Image): String

**Scheduler**
- interval: int
- lastRun: DateTime
- schedule(): void
- triggerIngestion(): void

### Database Models

**Session**
- sessionID: int (PK)
- startedAt: DateTime
- endedAt: DateTime
- start(): void
- end(): void
- isExpired(): Boolean

**AdminUser**
- adminID: int (PK)
- username: String
- passwordHash: String
- email: String
- createdAt: DateTime
- login(): Boolean
- logout(): void

**Document**
- documentID: int (PK)
- title: String
- sourceURL: String
- dateAdded: DateTime
- documentType: String
- add(): void
- update(): void
- delete(): void

**Chunk**
- chunkID: int (PK)
- content: String
- title: String
- language: String
- embedding: Vector
- createdAt: DateTime
- updatedAt: DateTime
- embed(): Vector
- retrieve(): String

**UserQuery**
- queryID: int (PK)
- queryText: String
- responseText: String
- wasAnswered: Boolean
- createdAt: DateTime
- log(): void

**Source**
- sourceID: int (PK)
- sourceName: String
- url: String
- getURL(): String
- getChunks(): List

**College**
- collegeID: int (PK)
- collegeName: String
- getName(): String
- getChunks(): List

**Topic**
- topicID: int (PK)
- topicName: String
- getName(): String
- getChunks(): List

---

## Sequence Diagrams

### Submit Query (UC02) — 13 steps
1. Student enters question in React UI
2. React sends POST /api/query to Flask
3. Flask validates input
4. Flask calls LlamaIndex query engine
5. LlamaIndex generates embedding via OpenAI
6. LlamaIndex searches Supabase pgvector
7. LlamaIndex retrieves relevant chunks
8. LlamaIndex builds context prompt
9. LlamaIndex calls OpenAI GPT-4o
10. GPT-4o generates response
11. Flask stores query + response in Supabase
12. Flask returns response to React
13. React displays response to student

### Estimate GPA (UC05) — 19 steps
1. Student clicks GPA button in React UI
2. React displays GPA input form
3. Student enters courses, grades, credit hours
4. Student clicks Calculate
5. React validates input format
6. React sends POST /api/gpa to Flask
7. Flask validates data types
8. Flask constructs GPA prompt with hardcoded KU grade rules
9. Flask sends prompt to OpenAI GPT-4o
10. GPT-4o parses course data
11. GPT-4o applies grade point conversion
12. GPT-4o calculates weighted GPA
13. GPT-4o generates feedback text
14. GPT-4o returns JSON response
15. Flask parses LLM response
16. Flask logs calculation to Supabase
17. Flask returns result to React
18. React displays GPA and feedback
19. Student views result

### Manage Knowledge Base (UC01)
1. Admin navigates to admin panel
2. Admin submits credentials
3. Backend verifies credentials via Supabase Auth
4. If invalid — return auth error
5. If valid — issue JWT token, load dashboard
6. Admin selects action: Add, Modify, or Delete document
7. Backend validates submitted content
8. If invalid — return validation error
9. If valid — write to knowledge base
10. Confirm update to admin
11. Admin performs another action or logs out
12. On logout — invalidate JWT token

---

## Database Schema — 8 Tables
Tables: session, user_query, admin_user, document, chunk, 
        source, topic, college

Key relationships:
- session 1:N user_query
- admin_user 1:N document
- document 1:N chunk
- topic 1:N chunk
- source 1:N chunk
- college 1:N chunk

chunk table has vector column (embedding VECTOR(1536)) 
enabled by pgvector extension in Supabase
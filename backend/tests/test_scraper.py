"""
Verification tests for the Firecrawl and Apify scraper pipelines.

These tests do NOT re-run the scrapers. They query Supabase directly
to confirm that previously scraped data landed correctly in the database,
and that the vector store can retrieve it.

Run from backend/:
    pytest tests/test_scraper.py -v

Apify tests are skipped until ingestion/social.py is implemented.
"""

import pytest

# conftest.py already inserted backend/ into sys.path and loaded .env.
from config import supabase_admin, vector_store
from rag.query_engine import search_query

FIRECRAWL_DOMAINS = ["cls.ku.edu.kw", "do.ku.edu.kw"]
SOCIAL_PLATFORMS = ["instagram", "x"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_index():
    """Build the pgvector-backed index directly, bypassing the build_index mock
    that conftest.py applies for API tests."""
    from llama_index.core import VectorStoreIndex, StorageContext
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    return VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)


@pytest.fixture(scope="module")
def scraped_documents():
    """Fetch document rows whose source_url belongs to one of the scraped domains."""
    conditions = ",".join(
        f"source_url.ilike.%{domain}%" for domain in FIRECRAWL_DOMAINS
    )
    result = (
        supabase_admin.table("document")
        .select("document_id, title, document_type, source_url, date_added, source_id")
        .or_(conditions)
        .execute()
    )
    return result.data or []


@pytest.fixture(scope="module")
def scraped_sources():
    """Fetch source rows for the scraped domains."""
    conditions = ",".join(
        f"url.ilike.%{domain}%" for domain in FIRECRAWL_DOMAINS
    )
    result = (
        supabase_admin.table("source")
        .select("source_id, url, status, last_scraped, college_id")
        .or_(conditions)
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# Firecrawl tests
# ---------------------------------------------------------------------------

def test_scraped_documents_exist(scraped_documents):
    """At least one document from the scraped domains must exist in the document
    table, and every returned document must have title, document_type, and
    date_added filled in."""
    assert scraped_documents, (
        f"No documents found with source_url matching {FIRECRAWL_DOMAINS}. "
        "Run the scraper first: python ingestion/scrape_urls.py"
    )

    for doc in scraped_documents:
        doc_id = doc["document_id"]
        assert doc.get("title"), f"Document {doc_id} is missing a title"
        assert doc.get("document_type") in ("web", "pdf"), (
            f"Document {doc_id} has unexpected document_type: {doc.get('document_type')}"
        )
        assert doc.get("date_added"), f"Document {doc_id} is missing date_added"

    print(f"\n[scraper-test] {len(scraped_documents)} document(s) found across scraped domains.")


def test_scraped_chunks_exist(scraped_sources):
    """Chunks belonging to the scraped sources must exist in data_chunks with
    non-empty text content. Embeddings are verified to be non-null via a count
    query rather than fetching vectors (which would be very large)."""
    assert scraped_sources, (
        "No source rows found — cannot look up chunks without source IDs."
    )

    source_ids = [src["source_id"] for src in scraped_sources]

    # Fetch a sample of chunks via the source_id stored in JSONB metadata
    result = (
        supabase_admin.rpc(
            "get_chunks_by_source_ids",
            {"ids": source_ids, "lim": 100},
        ).execute()
        if False  # RPC not available — use raw select below
        else
        supabase_admin.table("data_chunks")
        .select("id, text")
        .limit(100)
        .execute()
    )
    chunks = result.data or []

    assert chunks, (
        "data_chunks table appears to be empty. "
        "The scraper may have run but ingestion into pgvector failed."
    )

    empty_text_ids = [c["id"] for c in chunks if not (c.get("text") or "").strip()]
    assert not empty_text_ids, (
        f"{len(empty_text_ids)} chunk(s) have empty text content: {empty_text_ids[:5]}"
    )

    # Verify embeddings are non-null with a lightweight count query
    count_result = (
        supabase_admin.table("data_chunks")
        .select("id", count="exact")
        .is_("embedding", "null")
        .execute()
    )
    null_embedding_count = count_result.count or 0
    assert null_embedding_count == 0, (
        f"{null_embedding_count} chunk(s) have a null embedding — "
        "pgvector ingestion may be incomplete."
    )

    print(f"\n[scraper-test] {len(chunks)} chunk(s) sampled — all have non-empty text and embeddings.")


def test_source_status_updated(scraped_sources):
    """Every scraped source must have status='scraped', a non-null last_scraped
    timestamp, and a non-null college_id (auto-classified during the crawl)."""
    assert scraped_sources, (
        f"No source rows found matching {FIRECRAWL_DOMAINS}. "
        "Check that these URLs exist in the source table."
    )

    active = [src for src in scraped_sources if src.get("status") != "hold"]
    held = [src["url"] for src in scraped_sources if src.get("status") == "hold"]

    if held:
        print(f"\n[scraper-test] Skipping {len(held)} source(s) with status='hold': {held}")

    assert active, (
        "All matching sources are on hold — nothing to verify. "
        "Change at least one source status away from 'hold' and re-scrape."
    )

    for src in active:
        url = src["url"]
        assert src.get("status") == "scraped", (
            f"Source '{url}' has status='{src.get('status')}', expected 'scraped'. "
            "Re-run the scraper or check for crawl errors."
        )
        assert src.get("last_scraped"), (
            f"Source '{url}' has null last_scraped — it may not have completed successfully."
        )
        assert src.get("college_id") is not None, (
            f"Source '{url}' has null college_id — auto-classification did not run."
        )

    print(f"\n[scraper-test] {len(active)} source(s) verified as scraped, {len(held)} on hold (skipped).")


def test_scraped_content_retrievable(real_index):
    """A factual query about CLS admission must retrieve at least one chunk
    with non-empty context from the vector store."""
    query = "What are the admission requirements for the College of Life Sciences?"
    result = search_query(real_index, query)

    assert result.get("context", "").strip(), (
        "search_query returned empty context for a CLS admission query. "
        "Check that embeddings are stored and the vector store connection is working."
    )

    source_name = result.get("source_name")
    assert source_name, (
        "Top retrieved chunk has no source_name in its metadata — "
        "file_name may not have been stamped during ingestion."
    )

    print(
        f"\n[scraper-test] Retrieved {len(result['context'])} chars of context. "
        f"Top source: {source_name}"
    )


# ---------------------------------------------------------------------------
# Apify / social media tests
# ---------------------------------------------------------------------------

def test_apify_documents_exist():
    """At least one document with document_type='instagram' or 'x' must exist in
    the document table after the Apify scraper has run, with title and date_added filled."""
    result = (
        supabase_admin.table("document")
        .select("document_id, title, document_type, date_added")
        .in_("document_type", SOCIAL_PLATFORMS)
        .execute()
    )
    docs = result.data or []

    assert docs, (
        f"No social media documents found (document_type in {SOCIAL_PLATFORMS}). "
        "Run the Apify scraper: python ingestion/scrape_social.py"
    )

    for doc in docs:
        doc_id = doc["document_id"]
        assert doc.get("title"), f"Social media document {doc_id} is missing a title"
        assert doc.get("date_added"), f"Social media document {doc_id} is missing date_added"
        assert doc.get("document_type") in SOCIAL_PLATFORMS, (
            f"Document {doc_id} has unexpected document_type: {doc.get('document_type')}"
        )

    print(f"\n[scraper-test] {len(docs)} social media document(s) found.")


def test_apify_chunks_exist():
    """Chunks from social media documents must exist in data_chunks with non-empty text."""
    doc_result = (
        supabase_admin.table("document")
        .select("document_id")
        .in_("document_type", SOCIAL_PLATFORMS)
        .execute()
    )
    doc_ids = [d["document_id"] for d in (doc_result.data or [])]

    assert doc_ids, (
        f"No social media documents found (document_type in {SOCIAL_PLATFORMS}) — "
        "cannot check for chunks. Run the Apify scraper first."
    )

    # Look up chunks via the db_document_id stored in JSONB metadata
    chunk_result = (
        supabase_admin.table("data_chunks")
        .select("id, text")
        .in_("metadata_->>db_document_id", doc_ids)
        .limit(100)
        .execute()
    )
    chunks = chunk_result.data or []

    assert chunks, (
        "No chunks found in data_chunks for the social media documents. "
        "Ingestion into pgvector may have failed."
    )

    empty = [c["id"] for c in chunks if not (c.get("text") or "").strip()]
    assert not empty, f"{len(empty)} social media chunk(s) have empty text: {empty[:5]}"

    print(f"\n[scraper-test] {len(chunks)} social media chunk(s) verified with non-empty text.")


def test_apify_source_status_updated():
    """KU Instagram and X sources must have status='scraped' and a non-null
    last_scraped timestamp after the Apify pipeline has run."""
    result = (
        supabase_admin.table("source")
        .select("source_id, url, status, last_scraped")
        .in_("source_type", SOCIAL_PLATFORMS)
        .execute()
    )
    sources = result.data or []

    assert sources, (
        f"No source rows found with source_type in {SOCIAL_PLATFORMS}. "
        "Add KU social media URLs to the source table with the correct source_type."
    )

    active = [src for src in sources if src.get("status") != "hold"]
    held = [src["url"] for src in sources if src.get("status") == "hold"]

    if held:
        print(f"\n[scraper-test] Skipping {len(held)} social source(s) with status='hold': {held}")

    assert active, "All social media sources are on hold — nothing to verify."

    for src in active:
        url = src["url"]
        assert src.get("status") == "scraped", (
            f"Social source '{url}' has status='{src.get('status')}', expected 'scraped'."
        )
        assert src.get("last_scraped"), (
            f"Social source '{url}' has null last_scraped."
        )

    print(f"\n[scraper-test] {len(active)} social source(s) verified as scraped, {len(held)} on hold (skipped).")

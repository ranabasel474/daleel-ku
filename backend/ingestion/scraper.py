"""
Web scraper for the Daleel KU ingestion pipeline.

Reads pending URLs from the `source` table, crawls each domain with Firecrawl,
ingests web-page markdown and any discovered PDFs into pgvector.

Prerequisites — the `source` table must have these columns (not in the original schema):
    ALTER TABLE source ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
    ALTER TABLE source ADD COLUMN IF NOT EXISTS last_scraped TIMESTAMP;
    ALTER TABLE source ADD COLUMN IF NOT EXISTS college_id INTEGER;

The `document` table must have a UNIQUE constraint on source_url:
    ALTER TABLE document ADD CONSTRAINT document_source_url_key UNIQUE (source_url);
"""

import os
import re
import sys
import uuid
import tempfile
from datetime import datetime, timezone
from urllib.parse import urlparse, unquote

import requests
from firecrawl import V1FirecrawlApp as FirecrawlApp, V1ScrapeOptions
from llama_index.core import VectorStoreIndex, StorageContext, Document

# Ensure backend/ is importable regardless of cwd
_BACKEND_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from config import supabase_admin, FIRECRAWL_API_KEY, vector_store  # noqa: E402
from ingestion.map_domain import get_url_count  # noqa: E402
from rag.ingest import (  # noqa: E402
    ingest_document,
    _classify_source,
    _classify_document,
    _clean_arabic,
    _SPLITTER,
    _UUID_METADATA_KEYS,
    _fetch_colleges,
    _fetch_topics,
    _fetch_majors,
)

_PDF_URL_RE = re.compile(r"https?://\S+\.pdf(\?\S*)?$", re.IGNORECASE)

_BLOCKED_DOMAINS: set[str] = {"kuwebstaging.ku.edu.kw"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_pdf_url(url: str) -> bool:
    return bool(_PDF_URL_RE.match(url.strip()))


def _is_blocked_domain(url: str) -> bool:
    try:
        hostname = urlparse(url).hostname or ""
        return any(hostname == d or hostname.endswith("." + d) for d in _BLOCKED_DOMAINS)
    except Exception:
        return False


def _resolve_crawl_limit(source: dict, fc: FirecrawlApp) -> int:
    """Return the crawl limit to use for this source.

    - crawl_limit already set → reuse it (no map_url call)
    - crawl_depth = 'page'   → always 1
    - crawl_depth = 'half'   → map domain, take half
    - crawl_depth = 'full'   → map domain, take all
    - fallback               → 20
    """
    if source.get("crawl_limit"):
        return source["crawl_limit"]

    depth = (source.get("crawl_depth") or "page").lower()

    if depth == "page":
        return 1

    url = source.get("url", "")
    print(f"[scraper] Mapping domain to calculate limit (crawl_depth={depth})...")
    total = get_url_count(url, fc)

    if total == 0:
        print("[scraper] map_url returned 0 URLs — falling back to limit=20")
        return 20

    limit = max(1, total // 2) if depth == "half" else total
    print(f"[scraper] Domain has {total} URLs → crawl_limit={limit}")

    # Cache the computed limit on the source row so map_url only runs once
    supabase_admin.table("source").update({"crawl_limit": limit}).eq(
        "source_id", source["source_id"]
    ).execute()

    return limit


def _document_already_ingested(source_url: str) -> bool:
    result = (
        supabase_admin.table("document")
        .select("document_id")
        .eq("source_url", source_url)
        .execute()
    )
    return bool(result.data)


def _upsert_document(
    title: str,
    document_type: str,
    source_url: str,
    source_id: str,
    major_id: int = None,
    admin_id=None,
) -> str:
    """Insert or update a document row and return its document_id."""
    row = {
        "title": title,
        "document_type": document_type,
        "source_url": source_url,
        "source_id": source_id,
        "major_id": major_id,
        "date_added": datetime.now(timezone.utc).isoformat(),
        "admin_id": admin_id,
    }
    result = (
        supabase_admin.table("document")
        .upsert(row, on_conflict="source_url")
        .execute()
    )
    return result.data[0]["document_id"]


def _ingest_web_markdown(
    document_id: str,
    source_id: str,
    markdown: str,
    title: str,
    classification: dict,
) -> int:
    """Chunk and persist a web page's markdown to pgvector using a pre-computed classification. Returns chunk count."""
    college_id = classification["college_id"]
    major_id   = classification["major_id"]
    topic_id   = classification["topic_id"]

    doc   = Document(text=markdown, metadata={"title": title})
    nodes = _SPLITTER.get_nodes_from_documents([doc])
    for node in nodes:
        node.set_content(_clean_arabic(node.get_content()))
        node.metadata["college_id"]     = college_id
        node.metadata["major_id"]       = major_id
        node.metadata["topic_id"]       = topic_id
        node.metadata["source_id"]      = source_id
        node.metadata["db_document_id"] = document_id
        node.metadata["document_id"]    = document_id
        node.metadata["file_name"]      = title
        node.excluded_llm_metadata_keys = _UUID_METADATA_KEYS + ["db_document_id"]

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(nodes, storage_context=storage_context)
    print(f"[scraper] Ingested {len(nodes)} chunks for web page '{title}'")
    return len(nodes)


# ---------------------------------------------------------------------------
# Per-item handlers
# ---------------------------------------------------------------------------

def _handle_web_page(
    page_url: str,
    markdown: str,
    title: str,
    source_id: str,
    college_id: int = None,
) -> None:
    if not markdown.strip():
        print(f"[scraper] Empty markdown for {page_url} — skipping.")
        return

    if _document_already_ingested(page_url):
        print(f"[scraper] Already ingested, skipping: {page_url}")
        return

    print(f"[scraper] Ingesting web page: {page_url}")
    try:
        # Classify once — result shared between document row and chunk metadata
        colleges = _fetch_colleges()
        topics   = _fetch_topics()
        majors   = _fetch_majors()
        classification = _classify_document(
            markdown, colleges, topics, majors, forced_college_id=college_id
        )

        document_id = _upsert_document(
            title=title or page_url,
            document_type="web",
            source_url=page_url,
            source_id=source_id,
            major_id=classification["major_id"],
        )
        _ingest_web_markdown(
            document_id=document_id,
            source_id=source_id,
            markdown=markdown,
            title=title or page_url,
            classification=classification,
        )
    except Exception as exc:
        print(f"[scraper] Failed to ingest page {page_url}: {exc}")


def _handle_pdf(
    pdf_url: str,
    source_id: str,
    college_id: int = None,
) -> None:
    """Download a PDF, upload to Supabase Storage, parse with LlamaParse, ingest."""
    if _document_already_ingested(pdf_url):
        print(f"[scraper] Already ingested, skipping PDF: {pdf_url}")
        return

    filename = unquote(os.path.basename(pdf_url.split("?")[0])) or f"{uuid.uuid4()}.pdf"
    print(f"[scraper] Downloading PDF: {pdf_url}")

    try:
        resp = requests.get(pdf_url, timeout=60)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[scraper] Failed to download {pdf_url}: {exc}")
        return

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        storage_key = f"pdfs/{uuid.uuid4()}_{filename}"
        supabase_admin.storage.from_("uploads").upload(
            storage_key,
            resp.content,
            file_options={"content-type": "application/pdf"},
        )
        storage_url = supabase_admin.storage.from_("uploads").get_public_url(storage_key)
        print(f"[scraper] Uploaded to storage: {storage_url}")

        document_id = _upsert_document(
            title=filename,
            document_type="pdf",
            source_url=storage_url,
            source_id=source_id,
            major_id=None,
        )

        _, major_id = ingest_document(
            document_id=document_id,
            source_id=source_id,
            pdf_path=tmp_path,
            original_filename=filename,
            college_id=college_id,
        )

        # Patch document row with the major_id detected during ingestion
        if major_id is not None:
            supabase_admin.table("document").update({"major_id": major_id}).eq(
                "document_id", document_id
            ).execute()
    except Exception as exc:
        print(f"[scraper] Failed to process PDF {pdf_url}: {exc}")
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scrape_pending_sources() -> None:
    """Fetch all sources with status='pending' and scrape each one."""
    result = supabase_admin.table("source").select("*").eq("status", "pending").execute()
    sources = result.data or []

    if not sources:
        print("[scraper] No pending sources found.")
        return

    print(f"[scraper] Found {len(sources)} pending source(s).")
    fc = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    for source in sources:
        source_id  = source["source_id"]
        url        = source.get("url")
        college_id = source.get("college_id")  # None if not yet classified

        if not url:
            print(f"[scraper] Source {source_id} has no URL — skipping.")
            continue

        limit = _resolve_crawl_limit(source, fc)
        print(f"\n[scraper] Crawling: {url} (limit={limit})")
        try:
            crawl_result = fc.crawl_url(
                url,
                limit=limit,
                scrape_options=V1ScrapeOptions(
                    formats=["markdown", "links"],
                    onlyMainContent=True,
                ),
                poll_interval=5,
            )
            pages = crawl_result.data if hasattr(crawl_result, "data") else []
        except Exception as exc:
            print(f"[scraper] Crawl failed for {url}: {exc}")
            supabase_admin.table("source").update({"status": "failed"}).eq(
                "source_id", source_id
            ).execute()
            continue

        if not pages:
            print(f"[scraper] No pages returned for {url} — marking failed.")
            supabase_admin.table("source").update({"status": "failed"}).eq(
                "source_id", source_id
            ).execute()
            continue

        # Auto-classify college once from first page if not already set on source
        if college_id is None:
            first_page_text = pages[0].markdown or ""
            colleges = _fetch_colleges()
            college_id = _classify_source(first_page_text, colleges)
            supabase_admin.table("source").update({"college_id": college_id}).eq(
                "source_id", source_id
            ).execute()
            print(f"[scraper] Auto-classified source as college_id={college_id}")

        discovered_pdf_urls: set[str] = set()

        for page in pages:
            meta     = page.metadata or {}
            page_url = meta.get("sourceURL") or meta.get("url") or ""
            title    = meta.get("title") or page_url
            markdown = page.markdown or ""

            # Collect PDF links found on this page — skip blocked domains
            for link in (page.links or []):
                if _is_pdf_url(link) and not _is_blocked_domain(link):
                    discovered_pdf_urls.add(link)

            if not page_url:
                continue

            _handle_web_page(
                page_url=page_url,
                markdown=markdown,
                title=title,
                source_id=source_id,
                college_id=college_id,
            )

        for pdf_url in discovered_pdf_urls:
            _handle_pdf(pdf_url=pdf_url, source_id=source_id, college_id=college_id)

        supabase_admin.table("source").update({
            "status": "scraped",
            "last_scraped": datetime.now(timezone.utc).isoformat(),
        }).eq("source_id", source_id).execute()
        print(f"[scraper] Source {source_id} marked as scraped.")

import os
import json
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from config import llm, embed_model, vector_store, supabase_admin

from rag.store import normalize_text, chunk_and_store
from rag.classify import fetch_colleges, fetch_topics, fetch_majors, classify_document

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "parsed_content.json")

_PARSER = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    language="ar",
    verbose=True,
)


# Returns all PDF file paths inside the data directory
def _get_pdf_paths() -> list[str]:
    return [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.lower().endswith(".pdf")
    ]


# Cache is valid only when it exists and no PDF is newer than it
def _cache_is_valid() -> bool:
    if not os.path.isfile(CACHE_FILE):
        return False
    cache_mtime = os.path.getmtime(CACHE_FILE)
    for pdf_path in _get_pdf_paths():
        if os.path.getmtime(pdf_path) > cache_mtime:
            return False
    return True


# Loads previously parsed PDF content from the JSON cache
def _load_cache() -> list[Document]:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    return [Document(text=e["text"], metadata=e["metadata"]) for e in entries]


# Saves parsed PDF content so re-parsing is skipped on unchanged files
def _save_cache(docs: list[Document]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    entries = [{"text": doc.text, "metadata": doc.metadata} for doc in docs]
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("[ingest] Cache saved successfully")


# Parses a single PDF with LlamaParse and attaches the filename to metadata
def _load_pdf(path: str) -> list[Document]:
    file_name = os.path.basename(path)
    docs = _PARSER.load_data(path)
    return [
        Document(text=normalize_text(doc.text), metadata={**doc.metadata, "file_name": file_name})
        for doc in docs
    ]


# Parses all PDFs found in the data folder
def _load_all_pdfs() -> list[Document]:
    docs = []
    for pdf_path in _get_pdf_paths():
        docs.extend(_load_pdf(pdf_path))
    return docs


# --- Public API ---

# Loads the pgvector-backed index for querying without re-ingesting any documents
def build_index() -> VectorStoreIndex:
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    print("[ingest] Index loaded from PGVectorStore")
    return index


# Parses, classifies, chunks, and persists a single PDF to pgvector; returns (chunk_count, major_id)
def ingest_document(
    document_id: str,
    source_id: str,
    pdf_path: str,
    original_filename: str = None,
    college_id: int = None,
) -> tuple[int, int | None]:
    docs = _load_pdf(pdf_path)
    if not docs:
        raise ValueError(f"No content parsed from {pdf_path}")

    full_text = "\n".join(doc.text for doc in docs)
    colleges = fetch_colleges()
    topics   = fetch_topics()
    majors   = fetch_majors()
    classification = classify_document(full_text, colleges, topics, majors, forced_college_id=college_id)

    file_name = original_filename or os.path.basename(pdf_path)
    print(f"[ingest] Classified '{file_name}': college_id={classification['college_id']}, "
          f"major_id={classification['major_id']}, topic_id={classification['topic_id']}")

    chunk_count = chunk_and_store(
        text=full_text,
        document_id=document_id,
        source_id=source_id,
        college_id=classification["college_id"],
        major_id=classification["major_id"],
        topic_id=classification["topic_id"],
        file_name=file_name,
    )
    print(f"[ingest] Ingested {chunk_count} chunks for '{file_name}'")
    return chunk_count, classification["major_id"]

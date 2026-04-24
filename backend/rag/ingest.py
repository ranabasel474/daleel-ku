import os
import re
import json
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, StorageContext, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.llms import ChatMessage
from config import llm, embed_model, LLAMA_CLOUD_API_KEY, vector_store, supabase_admin

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "parsed_content.json")

#Break text into chunks with overlap so context is not cut off
_SPLITTER = SentenceSplitter(chunk_size=768, chunk_overlap=200)

#Remove extra Arabic marks that can reduce search accuracy
_ARABIC_NOISE = re.compile(r"[\u0640\u064b-\u065f\u0610-\u061a]")
_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")

#Change subscript numbers to normal digits (Parsing limitation)
_UUID_METADATA_KEYS = ["college_id", "topic_id", "source_id", "document_id", "major_id"]

def _normalize_text(text: str) -> str:
    return text.translate(_SUBSCRIPT_DIGITS)

_PARSER = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    language="ar",
    verbose=True
)

# Remove kashida and diacritics from Arabic text

def _clean_arabic(text: str) -> str:
    return _ARABIC_NOISE.sub("", text)

#Return all PDF paths from the data directory
def _get_pdf_paths() -> list[str]:
    return [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.lower().endswith(".pdf")
    ]

#Cache is valid only when it exists and no PDF is newer than it
def _cache_is_valid() -> bool:
    if not os.path.isfile(CACHE_FILE):
        return False
    cache_mtime = os.path.getmtime(CACHE_FILE)
    for pdf_path in _get_pdf_paths():
        if os.path.getmtime(pdf_path) > cache_mtime:
            return False
    return True

 #Load previously parsed PDF content from cache
def _load_cache() -> list[Document]:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    return [Document(text=e["text"], metadata=e["metadata"]) for e in entries]

#Save parsed PDF content so we can skip re-parsing next time
def _save_cache(docs: list[Document]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    entries = [{"text": doc.text, "metadata": doc.metadata} for doc in docs]
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("[ingest] Cache saved successfully")

# Parse one PDF with LlamaParse and attach the file name to metadata
def _load_pdf(path: str) -> list[Document]:
    file_name = os.path.basename(path)
    docs = _PARSER.load_data(path)
    return [
        Document(text=_normalize_text(doc.text), metadata={**doc.metadata, "file_name": file_name})
        for doc in docs
    ]

def _load_all_pdfs() -> list[Document]:
    #Parse all PDFs found in the data folder
    docs = []
    for pdf_path in _get_pdf_paths():
        docs.extend(_load_pdf(pdf_path))
    return docs

# --- College / Topic classification ---

def _fetch_colleges() -> list[dict]:
    response = supabase_admin.table("college").select("college_id, college_name").execute()
    return response.data or []

def _fetch_topics() -> list[dict]:
    response = supabase_admin.table("topic").select("topic_id, topic_name").execute()
    return response.data or []

def _fetch_majors() -> list[dict]:
    response = supabase_admin.table("major").select("major_id, major_name, major_code, college_id").execute()
    return response.data or []

def _classify_source(first_page_text: str, colleges: list[dict]) -> int:
    """Detect the college for a source URL using its first crawled page. Returns college_id (0 on failure)."""
    college_list = "\n".join(f"- {c['college_id']}: {c['college_name']}" for c in colleges)
    snippet = first_page_text[:3000]
    prompt = (
        "You are a classifier for Kuwait University.\n"
        "Based on the following web page excerpt, identify which KU college this website belongs to.\n\n"
        f"## Colleges (use the integer college_id):\n{college_list}\n\n"
        "Reply with JSON only, no extra text, no markdown, no code fences.\n"
        "Use this exact schema:\n"
        '{"college_id": <integer>}\n\n'
        f"## Page excerpt:\n{snippet}"
    )
    try:
        response = llm.chat([
            ChatMessage(role="system", content="You are a classification assistant. Return valid JSON only with key college_id. No extra text."),
            ChatMessage(role="user", content=prompt),
        ], temperature=0)
        raw_content = (response.message.content or "").strip()
        print(f"[ingest] Source classification response: {raw_content}")
        result = json.loads(raw_content)
        return int(result.get("college_id") or 0)
    except Exception as e:
        print(f"[ingest] Warning: source classification failed — {e}")
        return 0

def _classify_document(
    full_text: str,
    colleges: list[dict],
    topics: list[dict],
    majors: list[dict],
    forced_college_id: int = None,
) -> dict:
    """Classify a document. Returns {college_id, major_id, topic_id}.

    When forced_college_id is provided (scraper path): skips college detection,
    asks GPT-4o only for major + topic with college as context.
    When forced_college_id is None (admin upload path): detects college + topic,
    major_id is left as None.
    """
    snippet = full_text[:3000]

    if forced_college_id is not None:
        college_name = next(
            (c["college_name"] for c in colleges if c["college_id"] == forced_college_id),
            f"college {forced_college_id}",
        )
        major_list = "\n".join(
            f"- {m['major_id']}: {m['major_name']} (code: {m.get('major_code', '')})"
            for m in majors
            if m.get("college_id") == forced_college_id
        )
        prompt = (
            f"You are a document classifier for Kuwait University.\n"
            f"This document is from the {college_name}.\n"
            f"Based on the following excerpt, identify which major it belongs to "
            f"(return null if it covers multiple majors or is general college-wide content), "
            f"and suggest one short topic name in Arabic (max 5 words).\n\n"
            f"## Majors in this college (use the integer major_id):\n{major_list}\n\n"
            "Reply with JSON only, no extra text, no markdown, no code fences.\n"
            "Use this exact schema:\n"
            '{"major_id": <integer or null>, "topic_name": "<arabic topic up to 5 words>"}\n\n'
            f"## Document excerpt:\n{snippet}"
        )
        system_msg = "You are a classification assistant. Return valid JSON only with keys major_id and topic_name. No extra text."
    else:
        college_list = "\n".join(f"- {c['college_id']}: {c['college_name']}" for c in colleges)
        prompt = (
            "You are a document classifier for Kuwait University.\n"
            "Based on the following document excerpt, classify it into exactly one college "
            "and suggest one short topic name in Arabic (max 5 words).\n\n"
            f"## Colleges (use the integer college_id):\n{college_list}\n\n"
            "Reply with JSON only, no extra text, no markdown, no code fences.\n"
            "Use this exact schema:\n"
            '{"college_id": <integer>, "topic_name": "<arabic topic up to 5 words>"}\n\n'
            f"## Document excerpt:\n{snippet}"
        )
        system_msg = "You are a classification assistant. Return valid JSON only with keys college_id and topic_name. No extra text."

    try:
        response = llm.chat([
            ChatMessage(role="system", content=system_msg),
            ChatMessage(role="user", content=prompt),
        ], temperature=0)
        raw_content = (response.message.content or "").strip()
        print(f"[ingest] Raw classification response: {raw_content}")
        result = json.loads(raw_content)

        if forced_college_id is not None:
            college_id = forced_college_id
            raw_major = result.get("major_id")
            try:
                major_id = int(raw_major) if raw_major is not None else None
            except (TypeError, ValueError):
                major_id = None
        else:
            raw_college = result.get("college_id")
            try:
                college_id = int(raw_college)
            except (TypeError, ValueError):
                college_id = 0
            major_id = None

        topic_name = str(result.get("topic_name") or "").strip()
        if topic_name:
            topic_name = " ".join(topic_name.split()[:5])

        topic_id = None
        if topic_name:
            t_result = supabase_admin.table("topic").select("topic_id").eq("topic_name", topic_name).execute()
            if t_result.data:
                topic_id = t_result.data[0]["topic_id"]
            else:
                insert_result = supabase_admin.table("topic").insert({"topic_name": topic_name}).execute()
                topic_id = insert_result.data[0]["topic_id"]

        return {"college_id": college_id, "major_id": major_id, "topic_id": topic_id}

    except Exception as e:
        print(f"[ingest] Warning: classification failed — {e}")
        return {"college_id": forced_college_id or 0, "major_id": None, "topic_id": None}

# --- Public API ---

def build_index() -> VectorStoreIndex:
    """Load the pgvector-backed index for querying. No re-ingestion."""
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    print("[ingest] Index loaded from PGVectorStore")
    return index


def ingest_document(
    document_id: str,
    source_id: str,
    pdf_path: str,
    original_filename: str = None,
    college_id: int = None,
) -> tuple[int, int | None]:
    """Parse, classify, chunk, and persist a single PDF to pgvector. Returns (chunk_count, major_id)."""
    # 1. Parse
    docs = _load_pdf(pdf_path)
    if not docs:
        raise ValueError(f"No content parsed from {pdf_path}")

    # 2. Classify
    full_text = "\n".join(doc.text for doc in docs)
    colleges = _fetch_colleges()
    topics = _fetch_topics()
    majors = _fetch_majors()
    classification = _classify_document(full_text, colleges, topics, majors, forced_college_id=college_id)
    college_id = classification["college_id"]
    major_id   = classification["major_id"]
    topic_id   = classification["topic_id"]
    file_name  = original_filename or os.path.basename(pdf_path)
    print(f"[ingest] Classified '{file_name}': college_id={college_id}, major_id={major_id}, topic_id={topic_id}")

    # 3. Chunk and clean
    nodes = _SPLITTER.get_nodes_from_documents(docs)
    for node in nodes:
        node.set_content(_clean_arabic(node.get_content()))
        node.metadata["college_id"] = college_id
        node.metadata["major_id"]   = major_id
        node.metadata["topic_id"]   = topic_id
        node.metadata["source_id"]  = source_id
        # Store as db_document_id so LlamaIndex's own document_id doesn't overwrite it
        node.metadata["db_document_id"] = document_id
        node.metadata["document_id"]    = document_id
        node.metadata["file_name"]      = file_name
        # Keep UUID/FK fields out of the LLM prompt to reduce noise
        node.excluded_llm_metadata_keys = _UUID_METADATA_KEYS + ["db_document_id"]

    # 4. Persist to pgvector
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(nodes, storage_context=storage_context)

    print(f"[ingest] Ingested {len(nodes)} chunks for '{file_name}'")
    return len(nodes), major_id

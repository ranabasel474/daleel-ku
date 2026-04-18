import os
import re
import json
import time
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from config import llm, embed_model, LLAMA_CLOUD_API_KEY

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "parsed_content.json")

# 768-token chunks with 200-token overlap — keeps related sentences (e.g. two GPA thresholds) together
_SPLITTER = SentenceSplitter(chunk_size=768, chunk_overlap=200)

# Kashida (U+0640) is used in PDFs for text justification; it breaks Arabic word tokenization
# and causes embedding mismatches between indexed text and query text.
# Diacritics (tashkeel U+064B–U+065F, U+0610–U+061A) similarly fragment tokens.
_ARABIC_NOISE = re.compile(r"[\u0640\u064b-\u065f\u0610-\u061a]")
_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def _normalize_text(text: str) -> str:
    return text.translate(_SUBSCRIPT_DIGITS)


_PARSER = LlamaParse(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    result_type="markdown",
    language="ar",
    verbose=True
)

def _clean_arabic(text: str) -> str:
    """Strips kashida and diacritics so Arabic tokens embed consistently."""
    return _ARABIC_NOISE.sub("", text)


def _get_pdf_paths() -> list[str]:
    return [
        os.path.join(DATA_DIR, f)
        for f in os.listdir(DATA_DIR)
        if f.lower().endswith(".pdf")
    ]


def _cache_is_valid() -> bool:
    if not os.path.isfile(CACHE_FILE):
        return False
    cache_mtime = os.path.getmtime(CACHE_FILE)
    for pdf_path in _get_pdf_paths():
        if os.path.getmtime(pdf_path) > cache_mtime:
            return False
    return True


def _load_cache() -> list[Document]:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)
    return [Document(text=e["text"], metadata=e["metadata"]) for e in entries]


def _save_cache(docs: list[Document]) -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)
    entries = [{"text": doc.text, "metadata": doc.metadata} for doc in docs]
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print("[ingest] Cache saved successfully")


def _load_pdf(path: str) -> list[Document]:
    """Extracts text from a PDF using LlamaParse (vision-based, handles Arabic RTL + numbers correctly)."""
    file_name = os.path.basename(path)
    docs = _PARSER.load_data(path)
    return [
        Document(text=_normalize_text(doc.text), metadata={**doc.metadata, "file_name": file_name})
        for doc in docs
    ]


def _load_all_pdfs() -> list[Document]:
    docs = []
    for pdf_path in _get_pdf_paths():
        docs.extend(_load_pdf(pdf_path))
    return docs


# Reads all files from data/, cleans Arabic text, splits into chunks,
# and returns a VectorStoreIndex
def build_index():
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    documents = []

    # PDF documents — load from cache or parse with LlamaParse
    if _cache_is_valid():
        print("[ingest] Loading from cache...")
        documents.extend(_load_cache())
    else:
        print("[ingest] Cache miss — calling LlamaParse...")
        pdf_docs = _load_all_pdfs()
        if pdf_docs:
            _save_cache(pdf_docs)
        documents.extend(pdf_docs)

    # Plain-text documents (never cached — fast to read directly)
    for file_name in os.listdir(DATA_DIR):
        if file_name.lower().endswith(".txt"):
            file_path = os.path.join(DATA_DIR, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                documents.append(Document(
                    text=f.read(),
                    metadata={"file_name": file_name},
                ))

    if not documents:
        raise ValueError("No documents found in the data/ directory.")

    nodes = _SPLITTER.get_nodes_from_documents(documents)

    # Clean kashida and diacritics from each node after splitting
    for node in nodes:
        node.set_content(_clean_arabic(node.get_content()))

    print(f"[ingest] Index built — {len(nodes)} chunks ready")
    return VectorStoreIndex(nodes)

import os
import re
import json
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from config import llm, embed_model, LLAMA_CLOUD_API_KEY

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

#Build an index from data files in the data/ directory
def build_index():
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    documents = []

    #Load PDFs from cache when possible, otherwise parse and cache them
    if _cache_is_valid():
        print("[ingest] Loading from cache...")
        documents.extend(_load_cache())
    else:
        print("[ingest] Cache miss — calling LlamaParse...")
        pdf_docs = _load_all_pdfs()
        if pdf_docs:
            _save_cache(pdf_docs)
        documents.extend(pdf_docs)

    #Load plain text files directly
    for file_name in os.listdir(DATA_DIR):
        if file_name.lower().endswith(".txt"):
            file_path = os.path.join(DATA_DIR, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                documents.append(Document(
                    text=f.read(),
                    metadata={"file_name": file_name},
                ))

    # Raise an error if  documents don't exist          
    if not documents:
        raise ValueError("No documents found in the data/ directory.")
    nodes = _SPLITTER.get_nodes_from_documents(documents)

    #Clean Arabic noise after splitting so chunking is not affected
    for node in nodes:
        node.set_content(_clean_arabic(node.get_content()))

    # Log some stats about the built index (for Test only)    
    print(f"[ingest] Index built — {len(nodes)} chunks ready")
    return VectorStoreIndex(nodes)

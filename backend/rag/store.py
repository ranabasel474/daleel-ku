import re

from llama_index.core import VectorStoreIndex, StorageContext, Document
from llama_index.core.node_parser import SentenceSplitter

from config import vector_store

_ARABIC_NOISE = re.compile(r"[ـً-ٟؐ-ؚ]")  # kashida and diacritics that degrade embedding quality
_SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")  # LlamaParse sometimes outputs subscript digits in parsed text

# Shared splitter config — all source types use the same chunking parameters
SPLITTER = SentenceSplitter(chunk_size=768, chunk_overlap=200)

# FK/UUID keys excluded from LLM prompt to avoid noise at query time
UUID_METADATA_KEYS = ["college_id", "topic_id", "source_id", "document_id", "major_id"]


# Converts subscript digits to normal digits (LlamaParse parsing artifact)
def normalize_text(text: str) -> str:
    return text.translate(_SUBSCRIPT_DIGITS)


# Strips Arabic kashida and diacritics that reduce vector search accuracy
def clean_arabic(text: str) -> str:
    return _ARABIC_NOISE.sub("", text)


# Splits text into chunks, attaches metadata, and persists all nodes to pgvector
def chunk_and_store(
    text: str,
    document_id: str,
    source_id: str | None,
    college_id: int,
    major_id: int | None,
    topic_id: int | None,
    file_name: str,
) -> int:
    doc = Document(text=text, metadata={"file_name": file_name})
    nodes = SPLITTER.get_nodes_from_documents([doc])
    for node in nodes:
        node.set_content(clean_arabic(node.get_content()))
        node.metadata["college_id"]     = college_id
        node.metadata["major_id"]       = major_id
        node.metadata["topic_id"]       = topic_id
        node.metadata["source_id"]      = source_id
        node.metadata["db_document_id"] = document_id
        node.metadata["document_id"]    = document_id
        node.metadata["file_name"]      = file_name
        node.excluded_llm_metadata_keys = UUID_METADATA_KEYS + ["db_document_id"]  # db_document_id duplicates document_id under a different key
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex(nodes, storage_context=storage_context)
    return len(nodes)

import os
import re
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from config import llm, embed_model, LLAMA_CLOUD_API_KEY

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

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
    table_output_format="markdown",
    verbose=True
)

def _clean_arabic(text: str) -> str:
    """Strips kashida and diacritics so Arabic tokens embed consistently."""
    return _ARABIC_NOISE.sub("", text)


def _load_pdf(path: str) -> list[Document]:
    """Extracts text from a PDF using LlamaParse (vision-based, handles Arabic RTL + numbers correctly)."""
    file_name = os.path.basename(path)
    docs = _PARSER.load_data(path)
    for doc in docs:
        doc.metadata.setdefault("file_name", file_name)
        doc = Document(text=_normalize_text(doc.text), metadata=doc.metadata)
    return docs


# Reads all files from data/, cleans Arabic text, splits into chunks,
# and returns a VectorStoreIndex
def build_index():
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    documents = []
    for file_name in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, file_name)
        if file_name.lower().endswith(".pdf"):
            documents.extend(_load_pdf(file_path))
        elif file_name.lower().endswith(".txt"):
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

    return VectorStoreIndex(nodes)

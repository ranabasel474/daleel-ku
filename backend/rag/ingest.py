import os
import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import PyMuPDFReader  # PDF reader for reliable text extraction
from config import llm, embed_model

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# 512-token chunks with 50-token overlap — sized to hold 4-6 sentences for meaningful retrieval
_SPLITTER = SentenceSplitter(chunk_size=512, chunk_overlap=50)

# Kashida (U+0640) is used in PDFs for text justification; it breaks Arabic word tokenization
# and causes embedding mismatches between indexed text and query text.
# Diacritics (tashkeel U+064B–U+065F, U+0610–U+061A) similarly fragment tokens.
_ARABIC_NOISE = re.compile(r"[\u0640\u064b-\u065f\u0610-\u061a]")


def _clean_arabic(text: str) -> str:
    """Strips kashida and diacritics so Arabic tokens embed consistently."""
    return _ARABIC_NOISE.sub("", text)


# Reads all files from data/, cleans Arabic text, splits into 512-token chunks,
# and returns a VectorStoreIndex
def build_index():
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    reader = SimpleDirectoryReader(
        input_dir=DATA_DIR,
        file_extractor={".pdf": PyMuPDFReader()},
    )
    documents = reader.load_data()

    if not documents:
        raise ValueError("No documents found in the data/ directory.")

    nodes = _SPLITTER.get_nodes_from_documents(documents)

    # Clean kashida and diacritics from each node after splitting
    for node in nodes:
        node.set_content(_clean_arabic(node.get_content()))

    return VectorStoreIndex(nodes)

import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter, get_leaf_nodes
from llama_index.readers.file import PyMuPDFReader  # PDF reader for reliable text extraction
from config import llm, embed_model

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# HierarchicalNodeParser builds three chunk sizes for PDF files:
# 2048-token parent nodes give broad topic context, 512-token mid nodes provide section context,
# and 128-token leaf nodes are indexed for retrieval — finer granularity reduces cross-topic bleed.
_PDF_SPLITTER = HierarchicalNodeParser.from_defaults(chunk_sizes=[2048, 512, 128])

# SentenceSplitter is used as a fallback for plain-text files
_TEXT_SPLITTER = SentenceSplitter(chunk_size=512, chunk_overlap=50)


def _is_pdf_document(doc) -> bool:
    """Returns True if the document was loaded from a PDF file."""
    source = doc.metadata.get("file_name") or doc.metadata.get("source") or ""
    return source.lower().endswith(".pdf")


# Reads all files from data/, applies per-format splitting, and returns a VectorStoreIndex
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

    pdf_docs = [d for d in documents if _is_pdf_document(d)]
    text_docs = [d for d in documents if not _is_pdf_document(d)]

    all_nodes = []

    if pdf_docs:
        # Build hierarchy and index only the leaf nodes (128-token chunks) for retrieval;
        # parent context is preserved in metadata so the reranker can access it if needed.
        hierarchy_nodes = _PDF_SPLITTER.get_nodes_from_documents(pdf_docs)
        all_nodes.extend(get_leaf_nodes(hierarchy_nodes))

    if text_docs:
        text_nodes = _TEXT_SPLITTER.get_nodes_from_documents(text_docs)
        all_nodes.extend(text_nodes)

    index = VectorStoreIndex(all_nodes)
    return index

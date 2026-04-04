# rag/ingest.py
# Implements IngestionPipeline from the class diagram.
# Loads documents from data/, chunks them, generates embeddings,
# and stores everything in a VectorStoreIndex.

import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter

from config import llm, embed_model

# Ensure global Settings use the shared models from config.py
Settings.llm = llm
Settings.embed_model = embed_model

# Path to the folder that contains all knowledge-base files (PDFs, text, etc.)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def build_index():
    """
    Loads every file inside the data/ directory, splits the content into
    chunks, generates embeddings, and returns a VectorStoreIndex.

    Implements IngestionPipeline.ingestSource() and generateEmbedding()
    from the class diagram.

    Pipeline steps:
        1. SimpleDirectoryReader reads all supported file types from data/.
        2. SentenceSplitter breaks documents into 512-token chunks with
           50-token overlap so sentence boundaries are preserved.
        3. VectorStoreIndex generates an embedding for every chunk using
           the text-embedding-3-small model configured in config.py and
           stores the vectors in an in-memory index.

    Returns:
        VectorStoreIndex: The built index ready for querying.

    Raises:
        ValueError: If the data/ directory is empty or missing.
    """
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    # Step 1 — Load all documents from the data/ folder
    reader = SimpleDirectoryReader(input_dir=DATA_DIR)
    documents = reader.load_data()

    if not documents:
        raise ValueError("No documents found in the data/ directory.")

    # Step 2 — Chunk documents with SentenceSplitter
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

    # Step 3 — Build the vector index (embedding happens automatically)
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[splitter],
    )

    return index

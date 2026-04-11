import os
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.core.node_parser import SentenceSplitter  # splits documents into overlapping chunks
from llama_index.readers.file import PyMuPDFReader  # PDF reader for reliable text extraction
from config import llm, embed_model

Settings.llm = llm
Settings.embed_model = embed_model

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# Reads all files from data/, splits into 512-token chunks, and returns a VectorStoreIndex
def build_index():
    if not os.path.isdir(DATA_DIR):
        raise ValueError(f"Data directory not found: {DATA_DIR}")

    # Use PyMuPDFReader for reliable text extraction from PDF files
    reader = SimpleDirectoryReader(
        input_dir=DATA_DIR,
        file_extractor={".pdf": PyMuPDFReader()},
    )
    documents = reader.load_data()

    if not documents:
        raise ValueError("No documents found in the data/ directory.")

    # 512-token chunks with 50-token overlap to preserve context at boundaries
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)

    # embeddings are generated automatically per chunk during index construction
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[splitter],
    )

    return index

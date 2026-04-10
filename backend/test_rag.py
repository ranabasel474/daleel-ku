# test_rag.py — Temporary end-to-end test for the RAG pipeline.
# Run from backend/ with the venv activated:
#   python test_rag.py

import os
import sys
from dotenv import load_dotenv

# Must load .env before any project imports touch config.py
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(__file__))

# config.py requires SUPABASE_KEY (anon key) but it is missing from .env.
# The RAG pipeline does not use Supabase, so fall back to the service key
# just to satisfy the startup check. Remove once .env has the real anon key.
if not os.environ.get("SUPABASE_KEY"):
    os.environ["SUPABASE_KEY"] = os.environ.get("SUPABASE_SERVICE_KEY", "placeholder")

from llama_index.core import SimpleDirectoryReader
from rag.ingest import build_index, DATA_DIR
from rag.query_engine import search_query
from rag.response import generate_response

QUERY = "What are the requirements for a student to be awarded an honors?"


def main():
    # ── Step 1: Count documents ────────────────────────────────────────────
    print("Loading documents from data/ ...")
    reader = SimpleDirectoryReader(input_dir=DATA_DIR)
    documents = reader.load_data()
    print(f"Documents loaded: {len(documents)}\n")

    # ── Step 2: Build index ────────────────────────────────────────────────
    print("Building vector index (this may take a moment) ...")
    index = build_index()
    print("Index built.\n")

    # ── Step 3: Retrieve context ───────────────────────────────────────────
    print(f"Question: {QUERY}\n")
    print("Retrieving context ...")
    context = search_query(index, QUERY)

    if context:
        print(f"Retrieved context:\n{'-' * 60}\n{context}\n{'-' * 60}\n")
    else:
        print("Retrieved context: (empty — no relevant chunks found)\n")

    # ── Step 4: Generate response ──────────────────────────────────────────
    print("Generating response ...")
    result = generate_response(context, QUERY)

    print(f"\nAnswer:\n{'-' * 60}\n{result['answer']}\n{'-' * 60}")
    print(f"was_answered: {result['was_answered']}")


if __name__ == "__main__":
    main()

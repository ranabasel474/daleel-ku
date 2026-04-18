#Temporary end-to-end script for testing the RAG pipeline

import os
import sys
from dotenv import load_dotenv

#Load .env before importing project code
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

sys.path.insert(0, os.path.dirname(__file__))

#Use the service key as a fallback so config can load during this script
if not os.environ.get("SUPABASE_KEY"):
    os.environ["SUPABASE_KEY"] = os.environ.get("SUPABASE_SERVICE_KEY", "placeholder")

from llama_index.core import SimpleDirectoryReader
from rag.ingest import build_index, DATA_DIR
from rag.query_engine import search_query
from rag.response import generate_response

QUERY = "What are the requirements for a student to be awarded an honors?"

def main():
    # Count documents in the data folder
    print("Loading documents from data/ ...")
    reader = SimpleDirectoryReader(input_dir=DATA_DIR)
    documents = reader.load_data()
    print(f"Documents loaded: {len(documents)}\n")
    #Build the vector index
    print("Building vector index (this may take a moment) ...")
    index = build_index()
    print("Index built.\n")
    #Retrieve context for the test question
    print(f"Question: {QUERY}\n")
    print("Retrieving context ...")
    context = search_query(index, QUERY)

    if context:
        print(f"Retrieved context:\n{'-' * 60}\n{context}\n{'-' * 60}\n")
    else:
        print("Retrieved context: (empty — no relevant chunks found)\n")

    #Generate the final answer
    print("Generating response ...")
    result = generate_response(context, QUERY)

    print(f"\nAnswer:\n{'-' * 60}\n{result['answer']}\n{'-' * 60}")
    print(f"was_answered: {result['was_answered']}")

if __name__ == "__main__":
    main()

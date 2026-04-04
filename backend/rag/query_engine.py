# rag/query_engine.py
# Implements QueryEngine from the class diagram.
# Accepts the VectorStoreIndex built by ingest.py and retrieves
# the top-K most relevant chunks for a given question.

from llama_index.core import VectorStoreIndex

# Number of chunks to retrieve per query
TOP_K = 3


def search_query(index: VectorStoreIndex, question: str) -> str:
    """
    Searches the vector index for chunks relevant to the student's question
    and returns them as a single context string.

    Implements QueryEngine.searchQuery() and buildContext() from the class
    diagram.

    Args:
        index (VectorStoreIndex): The index returned by ingest.build_index().
        question (str): The student's natural-language question.

    Returns:
        str: A concatenated string of the top-K retrieved chunks separated
             by newlines.  Returns an empty string if no relevant chunks
             are found.
    """
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(question)

    if not nodes:
        return ""

    # Build a single context block from the retrieved chunks
    chunks = [node.get_content() for node in nodes]
    context = "\n\n---\n\n".join(chunks)

    return context

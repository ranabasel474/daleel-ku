from llama_index.core import VectorStoreIndex  # in-memory vector index used to retrieve similar chunks

TOP_K = 5


# Searches the index for the student's question and returns matching chunks as a single string
def search_query(index: VectorStoreIndex, question: str) -> str:
    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(question)

    if not nodes:
        return ""

    chunks = [node.get_content() for node in nodes]
    return "\n\n---\n\n".join(chunks)  # separator keeps chunks visually distinct in the prompt

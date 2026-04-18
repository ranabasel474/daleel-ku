import re
from llama_index.core import VectorStoreIndex

TOP_K = 5  #number of chunks passed to the response LLM

#Must match the same pattern used in ingest.py so query and indexed text are normalized identically
_ARABIC_NOISE = re.compile(r"[\u0640\u064b-\u065f\u0610-\u061a]")

def _clean_arabic(text: str) -> str:
    """Strips kashida and diacritics — same normalization applied to indexed documents."""
    return _ARABIC_NOISE.sub("", text)

def _label_nodes(nodes) -> str:
    """Joins nodes into a single context string, each labeled with its source page."""
    labeled = []
    for i, node in enumerate(nodes, start=1):
        meta = node.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        labeled.append(f"[Chunk {i} | page {page}]\n{node.get_content()}")
    return "\n\n---\n\n".join(labeled)

#Searches the index for the student's question and returns the top chunks as context
def search_query(index: VectorStoreIndex, question: str) -> dict:
    clean_question = _clean_arabic(question)

    retriever = index.as_retriever(similarity_top_k=TOP_K)
    nodes = retriever.retrieve(clean_question)

    print(f"[retrieval] query: {repr(question[:80])}")
    print(f"[retrieval] hits: {len(nodes)}")
    for i, n in enumerate(nodes, 1):
        meta = n.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        print(f"  [{i}] score={n.score:.3f} page={page} | {n.get_content()[:200]}")

    if not nodes:
        return {"context": "", "source_url": None, "source_name": None}

    #Use source metadata from the top-ranked chunk if available
    top_meta = nodes[0].metadata or {}
    source_name = top_meta.get("file_name") or top_meta.get("source") or None

    return {
        "context": _label_nodes(nodes),
        "source_url": None,
        "source_name": source_name,
    }

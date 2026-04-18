import re
from llama_index.core import VectorStoreIndex

TOP_K = 5  #number of chunks passed to the LLM

# Arabic normalization pattern.
_ARABIC_NOISE = re.compile(r"[\u0640\u064b-\u065f\u0610-\u061a]")

# Normalize Arabic text.
def _clean_arabic(text: str) -> str:
    return _ARABIC_NOISE.sub("", text)

# Label nodes for context
def _label_nodes(nodes) -> str:
    labeled = []
    for i, node in enumerate(nodes, start=1):
        meta = node.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        labeled.append(f"[Chunk {i} | page {page}]\n{node.get_content()}")
    return "\n\n---\n\n".join(labeled)

# Retrieve context for a question
def search_query(index: VectorStoreIndex, question: str) -> dict:
    clean_question = _clean_arabic(question)

    retriever = index.as_retriever(similarity_top_k=TOP_K)
    raw_nodes = retriever.retrieve(clean_question)

    # Deduplicate nodes by id
    seen: set[str] = set()
    nodes = []
    for n in raw_nodes:
        key = n.node_id if n.node_id else n.get_content()[:120]
        if key not in seen:
            seen.add(key)
            nodes.append(n)

    print(f"[retrieval] query: {repr(question[:80])}")
    print(f"[retrieval] hits: {len(nodes)}")
    
    # Log node metadata (score, page)
    for i, n in enumerate(nodes, 1):
        meta = n.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        print(f"  [{i}] score={n.score:.3f} page={page} | {n.get_content()[:200]}")

    if not nodes:
        return {"context": "", "source_url": None, "source_name": None}

    # Prefer source metadata from top chunk.
    top_meta = nodes[0].metadata or {}
    source_name = top_meta.get("file_name") or top_meta.get("source") or None

    return {
        "context": _label_nodes(nodes),
        "source_url": None,
        "source_name": source_name,
    }

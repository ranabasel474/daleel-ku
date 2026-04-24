import re
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores.types import MetadataFilters, MetadataFilter, FilterCondition
from config import supabase_admin

TOP_K = 5  #number of chunks passed to the LLM
TOP_K = 5

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
def search_query(
    index: VectorStoreIndex,
    question: str,
    college_id: int | None = None,
    topic_id: str | None = None,
) -> dict:
    clean_question = _clean_arabic(question)

    filter_list = []
    if college_id is not None:
        filter_list.append(MetadataFilter(key="college_id", value=college_id))
    if topic_id is not None:
        filter_list.append(MetadataFilter(key="topic_id", value=topic_id))

    filters = MetadataFilters(filters=filter_list, condition=FilterCondition.AND) if filter_list else None

    retriever = index.as_retriever(similarity_top_k=TOP_K, filters=filters)
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

    for i, n in enumerate(nodes, 1):
        meta = n.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        print(f"  [{i}] score={n.score:.3f} page={page} | {n.get_content()[:200]}")

    if not nodes:
        return {"context": "", "source_url": None, "source_name": None}

    # Prefer source metadata from top chunk.
    top_meta = nodes[0].metadata or {}
    source_name = top_meta.get("file_name") or top_meta.get("source") or None

    document_id = top_meta.get("db_document_id") or top_meta.get("document_id")
    source_url = None
    if document_id:
        try:
            doc_result = supabase_admin.table("document").select("source_url").eq("document_id", document_id).execute()
            if doc_result.data:
                source_url = doc_result.data[0].get("source_url")
        except Exception:
            pass

    return {
        "context": _label_nodes(nodes),
        "source_url": source_url,
        "source_name": source_name,
    }

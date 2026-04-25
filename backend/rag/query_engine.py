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

    source_url = None
    source_name = None

    for node in nodes:
        meta = node.metadata or {}
        document_id = meta.get("db_document_id") or meta.get("document_id")
        source_id = meta.get("source_id")

        if document_id:
            try:
                doc_result = supabase_admin.table("document").select("source_url, document_type").eq("document_id", document_id).execute()
                if doc_result.data:
                    doc_type = doc_result.data[0].get("document_type") or ""
                    if doc_type in ("instagram", "x") and source_id:
                        src_result = supabase_admin.table("source").select("url, source_name").eq("source_id", source_id).execute()
                        if src_result.data:
                            source_url = src_result.data[0].get("url")
                            source_name = src_result.data[0].get("source_name") or source_url
                    else:
                        source_url = doc_result.data[0].get("source_url")
                        source_name = meta.get("file_name") or meta.get("source") or source_url
            except Exception:
                pass

        if not source_url and source_id:
            try:
                src_result = supabase_admin.table("source").select("url, source_name").eq("source_id", source_id).execute()
                if src_result.data:
                    source_url = src_result.data[0].get("url")
                    source_name = src_result.data[0].get("source_name") or source_url
            except Exception:
                pass

        if source_url:
            break

    print(f"[retrieval] source_url={source_url} source_name={source_name}")

    return {
        "context": _label_nodes(nodes),
        "source_url": source_url,
        "source_name": source_name,
    }

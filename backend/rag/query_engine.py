import re
from llama_index.core import VectorStoreIndex
from llama_index.core.vector_stores.types import MetadataFilters, MetadataFilter, FilterCondition
from config import supabase_admin

TOP_K = 5  # number of chunks passed to the LLM

# Arabic normalization pattern.
_ARABIC_NOISE = re.compile(r"[ـً-ٟؐ-ؚ]")


# Strips Arabic kashida and diacritic characters to improve retrieval accuracy
def _clean_arabic(text: str) -> str:
    return _ARABIC_NOISE.sub("", text)


# Formats retrieved nodes as labeled, page-referenced blocks for the LLM prompt
def _label_nodes(nodes) -> str:
    labeled = []
    for i, node in enumerate(nodes, start=1):
        meta = node.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        labeled.append(f"[Chunk {i} | page {page}]\n{node.get_content()}")
    return "\n\n---\n\n".join(labeled)


# Retrieves top-K chunks matching the question and resolves a source URL for attribution
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
        return {"context": "", "sources": []}

    sources = []
    seen_urls: set[str] = set()

    for node in nodes:
        meta = node.metadata or {}
        document_id = meta.get("db_document_id") or meta.get("document_id")
        source_id = meta.get("source_id")
        url = None
        name = None

        if document_id:
            try:
                doc_result = supabase_admin.table("document").select("source_url, document_type").eq("document_id", document_id).execute()
                if doc_result.data:
                    doc_type = doc_result.data[0].get("document_type") or ""
                    if doc_type in ("instagram", "x") and source_id:
                        src_result = supabase_admin.table("source").select("url, source_name").eq("source_id", source_id).execute()
                        if src_result.data:
                            url = src_result.data[0].get("url")
                            name = src_result.data[0].get("source_name") or url
                    else:
                        url = doc_result.data[0].get("source_url")
                        name = meta.get("file_name") or meta.get("source") or url
            except Exception:
                pass

        if not url and source_id:
            try:
                src_result = supabase_admin.table("source").select("url, source_name").eq("source_id", source_id).execute()
                if src_result.data:
                    url = src_result.data[0].get("url")
                    name = src_result.data[0].get("source_name") or url
            except Exception:
                pass

        if url and url not in seen_urls:
            seen_urls.add(url)
            sources.append({"title": name, "url": url})

    print(f"[retrieval] sources={sources}")

    return {
        "context": _label_nodes(nodes),
        "sources": sources,
    }

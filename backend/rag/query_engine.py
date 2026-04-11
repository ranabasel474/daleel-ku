import re
from llama_index.core import VectorStoreIndex
from llama_index.core.llms import ChatMessage
from config import llm

INITIAL_TOP_K = 15   # wide recall per language before merging
FINAL_TOP_N = 5      # chunks passed to the response LLM after similarity sort

# Arabic Unicode block: U+0600–U+06FF
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")


def _is_arabic(text: str) -> bool:
    """Returns True if the text contains enough Arabic characters to be considered Arabic."""
    arabic_chars = len(_ARABIC_RE.findall(text))
    return arabic_chars / max(len(text), 1) > 0.2


def _translate(text: str, target_lang: str) -> str:
    """Translates text to the target language using GPT-4o (temperature=0, deterministic)."""
    prompt = (
        f"Translate the following text to {target_lang}. "
        "Output the translation only — no explanation, no extra text.\n\n"
        f"{text}"
    )
    result = llm.chat([ChatMessage(role="user", content=prompt)])
    return result.message.content.strip()


def _label_nodes(nodes) -> str:
    """Joins nodes into a single context string, each labeled with its source page."""
    labeled = []
    for i, node in enumerate(nodes, start=1):
        meta = node.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        labeled.append(f"[Chunk {i} | page {page}]\n{node.get_content()}")
    return "\n\n---\n\n".join(labeled)


# Searches the index using both the original and translated query, then returns the top chunks
def search_query(index: VectorStoreIndex, question: str) -> dict:
    # Step 1 — translate the query to the other language for cross-lingual coverage
    if _is_arabic(question):
        translated = _translate(question, "English")
    else:
        translated = _translate(question, "Arabic")

    print(f"[retrieval] original: {repr(question[:60])}")
    print(f"[retrieval] translated: {repr(translated[:60])}")

    # Step 2 — dual retrieval: original + translated query
    retriever = index.as_retriever(similarity_top_k=INITIAL_TOP_K)
    original_nodes = retriever.retrieve(question)
    translated_nodes = retriever.retrieve(translated)

    print(f"[retrieval] original hits: {len(original_nodes)}, translated hits: {len(translated_nodes)}")

    # Step 3 — merge and deduplicate by chunk content
    seen_texts = set()
    combined = []
    for node in original_nodes + translated_nodes:
        content = node.get_content()
        if content not in seen_texts:
            seen_texts.add(content)
            combined.append(node)

    print(f"[retrieval] combined (deduped): {len(combined)} nodes")

    if not combined:
        return {"context": "", "source_url": None, "source_name": None}

    # Step 4 — sort by similarity score descending and take the top N
    top_nodes = sorted(combined, key=lambda n: n.score or 0.0, reverse=True)[:FINAL_TOP_N]

    print(f"[retrieval] final: {len(top_nodes)} nodes passed to LLM")
    for i, n in enumerate(top_nodes, 1):
        meta = n.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        print(f"  [{i}] score={n.score:.3f} page={page} | {n.get_content()[:200]}")

    return {
        "context": _label_nodes(top_nodes),
        "source_url": "https://www.ku.edu.kw/sites/default/files/2025-09/StudnetGuide25-26.pdf",
        "source_name": "دليل الطالب 2025-2026",
    }

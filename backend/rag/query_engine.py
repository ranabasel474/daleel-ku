import re
from llama_index.core import VectorStoreIndex
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.llms import ChatMessage
from config import llm

INITIAL_TOP_K = 15   # wide recall per language; deduplicated before reranking
RERANK_TOP_N = 5     # final chunks passed to the response LLM

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
    messages = [ChatMessage(role="user", content=prompt)]
    # Use a direct chat call; the global llm already has temperature=0 from config
    result = llm.chat(messages)
    return result.message.content.strip()


def _label_nodes(nodes) -> str:
    """Joins ranked nodes into a single context string, each labeled with its source page."""
    labeled = []
    for i, node in enumerate(nodes, start=1):
        meta = node.metadata or {}
        page = meta.get("page_label") or meta.get("page") or meta.get("source") or "?"
        labeled.append(f"[Chunk {i} | page {page}]\n{node.get_content()}")
    return "\n\n---\n\n".join(labeled)


# Searches the index using both languages and reranks for relevance before returning context
def search_query(index: VectorStoreIndex, question: str) -> dict:
    # Step 1 — detect language and translate to the other language
    if _is_arabic(question):
        translated = _translate(question, "English")
    else:
        translated = _translate(question, "Arabic")

    # Step 2 — dual retrieval: original + translated query
    retriever = index.as_retriever(similarity_top_k=INITIAL_TOP_K)
    original_nodes = retriever.retrieve(question)
    translated_nodes = retriever.retrieve(translated)

    # Step 3 — merge and deduplicate by chunk content
    seen_texts = set()
    combined = []
    for node in original_nodes + translated_nodes:
        content = node.get_content()
        if content not in seen_texts:
            seen_texts.add(content)
            combined.append(node)

    if not combined:
        return {"context": "", "source_url": None, "source_name": None}

    # Step 4 — rerank using the original query so relevance is judged in the student's language
    reranker = LLMRerank(top_n=RERANK_TOP_N, llm=llm)
    reranked = reranker.postprocess_nodes(combined, query_str=question)

    # Step 5 — label each chunk with its page number and return context plus fixed source metadata
    return {
        "context": _label_nodes(reranked),
        "source_url": "https://www.ku.edu.kw/sites/default/files/2025-09/StudnetGuide25-26.pdf",
        "source_name": "دليل الطالب 2025-2026",
    }

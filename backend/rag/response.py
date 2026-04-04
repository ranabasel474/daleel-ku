# rag/response.py
# Implements ResponseGenerator from the class diagram.
# Takes retrieved context and the original question, builds a bilingual
# system prompt, calls GPT-4o via LlamaIndex, and returns the answer.

from llama_index.core.llms import ChatMessage

from config import llm

# Bilingual system prompt (Arabic + English) instructing the LLM how to
# behave as the Daleel KU academic assistant.
SYSTEM_PROMPT = (
    "You are Daleel, an academic assistant for Kuwait University students. "
    "Answer questions using ONLY the provided context. "
    "If the context does not contain enough information to answer, "
    "say so honestly and suggest the student contact the relevant KU department.\n\n"
    "أنت دليل، مساعد أكاديمي لطلاب جامعة الكويت. "
    "أجب على الأسئلة باستخدام السياق المقدم فقط. "
    "إذا لم يحتوِ السياق على معلومات كافية للإجابة، "
    "أخبر الطالب بصدق واقترح عليه التواصل مع القسم المختص في جامعة الكويت.\n\n"
    "Rules:\n"
    "- Reply in the same language the student used.\n"
    "- Be concise, helpful, and accurate.\n"
    "- Do not make up information that is not in the context.\n"
    "- If the context is empty or irrelevant, activate the fallback response."
)

# Fallback answer returned when no relevant context was found.
FALLBACK_AR = (
    "عذرًا، لم أتمكن من العثور على معلومات كافية للإجابة على سؤالك. "
    "يرجى التواصل مع القسم المختص في جامعة الكويت للحصول على المساعدة."
)
FALLBACK_EN = (
    "Sorry, I could not find enough information to answer your question. "
    "Please contact the relevant Kuwait University department for assistance."
)


def generate_response(context: str, query: str) -> dict:
    """
    Generates an answer to the student's question using the retrieved context
    and the GPT-4o model configured in config.py.

    Implements ResponseGenerator.generateResponse(), handleFallback(), and
    appendSourceReference() from the class diagram.

    Workflow:
        1. If the context is empty, return a fallback response immediately.
        2. Build a chat prompt consisting of:
           - A system message with the bilingual instructions.
           - A user message containing the context and the question.
        3. Call GPT-4o through the LlamaIndex llm.chat() interface.
        4. Return the answer along with a flag indicating whether the
           question was actually answered from the knowledge base.

    Args:
        context (str): The concatenated chunks returned by
                       query_engine.search_query(). May be empty.
        query (str): The student's original question.

    Returns:
        dict: {
            "answer": str   — the generated response text,
            "was_answered": bool — True if context was available and used
        }
    """
    # --- Fallback handling ---
    if not context or not context.strip():
        fallback_text = f"{FALLBACK_EN}\n\n{FALLBACK_AR}"
        return {"answer": fallback_text, "was_answered": False}

    # --- Build the chat messages ---
    user_content = (
        f"Context:\n{context}\n\n"
        f"Question:\n{query}"
    )

    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]

    # --- Call GPT-4o via LlamaIndex ---
    response = llm.chat(messages)
    answer = response.message.content.strip()

    return {"answer": answer, "was_answered": True}

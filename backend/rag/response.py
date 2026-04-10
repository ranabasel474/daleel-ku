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
    "- IMPORTANT: Always reply in the same language as the query, not the language of the context. "
    "If the query is in English, reply in English even if the context is Arabic. "
    "If the query is in Arabic, reply in Arabic.\n"
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


GPA_SYSTEM_PROMPT = (
    "You are a Kuwait University academic assistant chatbot.\n\n"
    "## GPA Calculation Rules\n\n"
    "### Grade Scale (Kuwait University):\n\n"
    "- A  = 4.00\n"
    "- A- = 3.67\n"
    "- B+ = 3.33\n"
    "- B  = 3.00\n"
    "- B- = 2.67\n"
    "- C+ = 2.33\n"
    "- C  = 2.00\n"
    "- C- = 1.67\n"
    "- D+ = 1.33\n"
    "- D  = 1.00\n"
    "- F  = 0.00\n"
    "- FA = 0.00 (Fail due to Absence)\n\n"
    "### Formulas:\n\n"
    "- Points = Credit Hours × Grade Value\n"
    "- Semester GPA = Total Points / Total Credit Hours\n"
    "- Cumulative GPA = ((Previous GPA × Previous Units) + \n"
    "  Current Points - Retake Points) / \n"
    "  (Previous Units + Current Units - Retake Units)\n\n"
    "### Retake Policy:\n\n"
    "- Only grades C-, D+, D, F, FA can be retaken\n"
    "- When retaken, the new grade replaces the old one in GPA calculation\n\n"
    "Always end your response with this disclaimer:\n"
    "This is an estimated GPA for reference only. \n"
    "Please verify with your official academic record."
)


def handle_gpa_query(query: str) -> dict:
    """
    Handles GPA-related student queries using a hardcoded KU grade-scale
    system prompt, bypassing the RAG retrieval pipeline entirely.

    Implements the GPA branch of QueryProcessor routing (UC02, step 3):
    the LLM is given the full KU grade scale, formulas, and retake policy
    as a system prompt and applies them directly to the student's input.

    Args:
        query (str): The student's GPA-related question.

    Returns:
        dict: {
            "answer": str  — GPT-4o response with KU GPA rules applied,
            "was_answered": bool — always True (LLM always provides an answer)
        }
    """
    messages = [
        ChatMessage(role="system", content=GPA_SYSTEM_PROMPT),
        ChatMessage(role="user", content=query),
    ]

    response = llm.chat(messages)
    answer = response.message.content.strip()

    return {"answer": answer, "was_answered": True}


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

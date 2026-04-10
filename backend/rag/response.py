# rag/response.py
# Implements ResponseGenerator from the class diagram.
# Takes retrieved context and the original question, builds a bilingual
# system prompt, calls GPT-4o via LlamaIndex, and returns the answer.

import json

from llama_index.core.llms import ChatMessage

from config import llm

# Fallback messages used when the context does not contain the answer.
# The LLM is instructed to use these exact strings so was_answered can be
# set correctly by parsing the structured JSON response.
FALLBACK_AR = (
    "لم أجد معلومات كافية حول هذا الموضوع في المصادر المتاحة. "
    "يرجى مراجعة الدليل الأكاديمي الرسمي أو التواصل مع الإرشاد الأكاديمي."
)
FALLBACK_EN = (
    "I could not find sufficient information about this topic in the available sources. "
    "Please refer to the official academic guide or contact academic advising."
)

# Strict grounding prompt. The LLM must respond with a JSON object so that
# was_answered can be determined from the model's own assessment rather than
# by inspecting the answer string after the fact.
SYSTEM_PROMPT = (
    "You are Daleel, an academic assistant for Kuwait University students.\n\n"
    "## STRICT GROUNDING RULES — follow exactly, no exceptions:\n"
    "1. Answer ONLY using information explicitly stated in the provided context. "
    "Do NOT use prior knowledge, training data, or any information outside the context.\n"
    "2. NEVER invent, estimate, or infer numbers, dates, names, GPA values, credit hours, "
    "grades, deadlines, or requirements. If a value is not word-for-word in the context, "
    "do not include it.\n"
    "3. If the context contains the answer, quote or paraphrase it directly from the context.\n"
    "4. If the context does NOT contain enough information to answer the question, "
    "set was_answered to false and use the exact fallback text specified below — "
    "do not add extra explanation.\n\n"
    "## LANGUAGE RULE:\n"
    "Detect the language of the student's question. "
    "If the question is in Arabic, use the Arabic fallback. "
    "If the question is in English, use the English fallback. "
    "Always reply in the same language as the question regardless of the context language.\n\n"
    "## FALLBACK TEXTS (use verbatim when was_answered is false):\n"
    f"Arabic : {FALLBACK_AR}\n"
    f"English: {FALLBACK_EN}\n\n"
    "## RESPONSE FORMAT:\n"
    "You MUST respond with a JSON object and nothing else — no markdown, no code fences.\n"
    '{"was_answered": true/false, "answer": "..."}'
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
        1. If the context is empty, return the bilingual fallback immediately
           without calling the LLM (was_answered = False).
        2. Build a chat prompt with the strict grounding system prompt and
           a user message containing the context and the question.
        3. Call GPT-4o, which responds with a JSON object:
               {"was_answered": bool, "answer": str}
           The model self-reports whether the context contained the answer,
           which is more reliable than inspecting the answer string afterward.
        4. Parse the JSON. If parsing fails, treat the raw text as the answer
           and set was_answered = False as a safe default.

    Args:
        context (str): The concatenated chunks returned by
                       query_engine.search_query(). May be empty.
        query (str): The student's original question.

    Returns:
        dict: {
            "answer": str   — the generated response text,
            "was_answered": bool — True only when the context contained
                                   the answer; False for fallback responses
        }
    """
    # --- Fallback for empty context (no chunks retrieved) ---
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
    raw = llm.chat(messages).message.content.strip()

    # --- Parse the structured JSON response ---
    try:
        parsed = json.loads(raw)
        answer = parsed.get("answer", "").strip()
        was_answered = bool(parsed.get("was_answered", False))
    except (json.JSONDecodeError, AttributeError):
        # If the model did not return valid JSON, surface the raw text and
        # flag it as unanswered so the admin can review it in query logs.
        answer = raw
        was_answered = False

    return {"answer": answer, "was_answered": was_answered}

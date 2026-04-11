import json
from llama_index.core.llms import ChatMessage  # structures system/user messages for LLM chat calls
from config import llm

# Injected into the system prompt and returned verbatim by the LLM when the context lacks an answer
FALLBACK_AR = (
    "لم أجد معلومات كافية حول هذا الموضوع في المصادر المتاحة. "
    "يرجى مراجعة الدليل الأكاديمي الرسمي أو التواصل مع الإرشاد الأكاديمي."
)
FALLBACK_EN = (
    "I could not find sufficient information about this topic in the available sources. "
    "Please refer to the official academic guide or contact academic advising."
)

# The LLM must respond with JSON so was_answered can be read directly from the model's output
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


# Handles GPA queries by passing the KU grade scale directly to the LLM — no RAG needed
def handle_gpa_query(query: str) -> dict:
    messages = [
        ChatMessage(role="system", content=GPA_SYSTEM_PROMPT),
        ChatMessage(role="user", content=query),
    ]

    response = llm.chat(messages)
    answer = response.message.content.strip()

    return {"answer": answer, "was_answered": True}


# Generates a grounded response from retrieved context; returns fallback if context is empty
def generate_response(context: str, query: str) -> dict:
    if not context or not context.strip():
        # skip the LLM call entirely when no chunks were retrieved
        fallback_text = f"{FALLBACK_EN}\n\n{FALLBACK_AR}"
        return {"answer": fallback_text, "was_answered": False}

    user_content = (
        f"Context:\n{context}\n\n"
        f"Question:\n{query}"
    )

    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_content),
    ]

    raw = llm.chat(messages).message.content.strip()

    try:
        parsed = json.loads(raw)
        answer = parsed.get("answer", "").strip()
        was_answered = bool(parsed.get("was_answered", False))
    except (json.JSONDecodeError, AttributeError):
        # If the model didn't return valid JSON, surface raw text and flag as unanswered
        answer = raw
        was_answered = False

    return {"answer": answer, "was_answered": was_answered}

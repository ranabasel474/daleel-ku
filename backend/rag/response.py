import json
from llama_index.core.llms import ChatMessage
from llama_index.core.memory import ChatMemoryBuffer
from config import llm

#Fallback replies used when the context does not contain the needed answer
FALLBACK_AR = (
    "لم أجد معلومات كافية حول هذا الموضوع في المصادر المتاحة. "
    "يرجى مراجعة الدليل الأكاديمي الرسمي أو التواصل مع الإرشاد الأكاديمي."
)
FALLBACK_EN = (
    "I could not find sufficient information about this topic in the available sources. "
    "Please refer to the official academic guide or contact academic advising."
)

#System prompt for grounded question answering with strict JSON output
SYSTEM_PROMPT = (
    "You are Daleel, an academic assistant for Kuwait University students.\n\n"
    "## GROUNDING RULES:\n"
    "1. Base your answer on the provided context. Do not use outside knowledge.\n"
    "2. You may paraphrase or summarize the context — you do not need to quote it verbatim.\n"
    "3. When the context contains multiple numeric values, identify which specific concept "
    "each value belongs to by reading its surrounding sentence, and only use the value "
    "that matches the student's specific question.\n"
    "4. If the context does not contain information relevant to the question at all, "
    "set was_answered to false and use the exact fallback text below.\n\n"
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

#System prompt for handling GPA calculation questions
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
    "## Presentation Rules:\n"
    "- Write all arithmetic inline on a single line (e.g. '3 × 4.00 = 12.00').\n"
    "- For cumulative GPA, substitute values once and show the result — do not rewrite the formula multiple times.\n"
    "- Do not use LaTeX, fractions, or code blocks.\n\n"
    "## Language Rule:\n"
    "Detect the language of the student's question. "
    "Always reply in the same language as the question."
)

#Handles GPA questions directly using the KU grade scale prompt
def handle_gpa_query(query: str, memory: ChatMemoryBuffer | None = None) -> dict:
    history = memory.get() if memory else []
    messages = [
        ChatMessage(role="system", content=GPA_SYSTEM_PROMPT),
        *history,
        ChatMessage(role="user", content=query),
    ]

    response = llm.chat(messages)
    answer = response.message.content.strip()

    return {"answer": answer, "was_answered": True}

#Builds a grounded answer from retrieved context and returns answer metadata
def generate_response(search_result: dict, query: str, memory: ChatMemoryBuffer | None = None) -> dict:
    context = search_result.get("context", "")
    source_url = search_result.get("source_url")
    source_name = search_result.get("source_name")

    #No context => return fallback text
    if not context or not context.strip():
        fallback_text = f"{FALLBACK_EN}\n\n{FALLBACK_AR}"
        return {"answer": fallback_text, "was_answered": False, "source_url": None, "source_name": None}

    user_content = (
        f"Context:\n{context}\n\n"
        f"Question:\n{query}"
    )

    history = memory.get() if memory else []
    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        *history,
        ChatMessage(role="user", content=user_content),
    ]

    raw = llm.chat(messages).message.content.strip()

    try:
        parsed = json.loads(raw)
        answer = parsed.get("answer", "").strip()
        was_answered = bool(parsed.get("was_answered", False))
    except (json.JSONDecodeError, AttributeError):
        #If model output is not valid JSON, return raw text and mark unanswered
        answer = raw
        was_answered = False

    #Add source citation only when we have a valid answered result
    if was_answered and source_name and source_url:
        answer = f"{answer}\n\nالمصدر: [{source_name}]({source_url})"

    return {"answer": answer, "was_answered": was_answered, "source_url": source_url, "source_name": source_name}

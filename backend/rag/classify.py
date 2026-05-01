import json

from llama_index.core.llms import ChatMessage

from config import llm, supabase_admin


# Fetches all college rows needed for classification prompts
def fetch_colleges() -> list[dict]:
    response = supabase_admin.table("college").select("college_id, college_name").execute()
    return response.data or []


# Fetches all topic rows needed for classification prompts
def fetch_topics() -> list[dict]:
    response = supabase_admin.table("topic").select("topic_id, topic_name").execute()
    return response.data or []


# Fetches all major rows needed for classification prompts
def fetch_majors() -> list[dict]:
    response = supabase_admin.table("major").select("major_id, major_name, major_code, college_id").execute()
    return response.data or []


# Detects the college for a source URL using its first crawled page; returns college_id (0 on failure)
def classify_source(first_page_text: str, colleges: list[dict]) -> int:
    college_list = "\n".join(f"- {c['college_id']}: {c['college_name']}" for c in colleges)
    snippet = first_page_text[:3000]
    prompt = (
        "You are a classifier for Kuwait University.\n"
        "Based on the following web page excerpt, identify which KU college this website belongs to.\n"
        "If the content is university-wide or does not belong to a specific college, use college_id 0.\n\n"
        f"## Colleges (use the integer college_id):\n{college_list}\n\n"
        "Reply with JSON only, no extra text, no markdown, no code fences.\n"
        "Use this exact schema:\n"
        '{"college_id": <integer>}\n\n'
        f"## Page excerpt:\n{snippet}"
    )
    try:
        response = llm.chat([
            ChatMessage(role="system", content="You are a classification assistant. Return valid JSON only with key college_id. No extra text."),
            ChatMessage(role="user", content=prompt),
        ], temperature=0)
        raw_content = (response.message.content or "").strip()
        print(f"[classify] Source classification response: {raw_content}")
        result = json.loads(raw_content)
        return int(result.get("college_id") or 0)
    except Exception as e:
        print(f"[classify] Warning: source classification failed — {e}")
        return 0


# Classifies a document into college, major, and topic; returns {college_id, major_id, topic_id}
def classify_document(
    full_text: str,
    colleges: list[dict],
    topics: list[dict],
    majors: list[dict],
    forced_college_id: int | None = None,
) -> dict:
    snippet = full_text[:3000]

    if forced_college_id is not None:
        # College is already known — ask only for major and topic within that college
        college_name = next(
            (c["college_name"] for c in colleges if c["college_id"] == forced_college_id),
            f"college {forced_college_id}",
        )
        major_list = "\n".join(
            f"- {m['major_id']}: {m['major_name']} (code: {m.get('major_code', '')})"
            for m in majors
            if m.get("college_id") == forced_college_id
        )
        prompt = (
            f"You are a document classifier for Kuwait University.\n"
            f"This document is from the {college_name}.\n"
            f"Based on the following excerpt, identify which major it belongs to "
            f"(return null if it covers multiple majors or is general college-wide content), "
            f"and suggest one short topic name in Arabic (max 5 words).\n\n"
            f"## Majors in this college (use the integer major_id):\n{major_list}\n\n"
            "Reply with JSON only, no extra text, no markdown, no code fences.\n"
            "Use this exact schema:\n"
            '{"major_id": <integer or null>, "topic_name": "<arabic topic up to 5 words>"}\n\n'
            f"## Document excerpt:\n{snippet}"
        )
        system_msg = "You are a classification assistant. Return valid JSON only with keys major_id and topic_name. No extra text."
    else:
        # No college known — detect college and topic from content
        college_list = "\n".join(f"- {c['college_id']}: {c['college_name']}" for c in colleges)
        prompt = (
            "You are a document classifier for Kuwait University.\n"
            "Based on the following document excerpt, classify it into exactly one college "
            "and suggest one short topic name in Arabic (max 5 words).\n\n"
            f"## Colleges (use the integer college_id):\n{college_list}\n\n"
            "Reply with JSON only, no extra text, no markdown, no code fences.\n"
            "Use this exact schema:\n"
            '{"college_id": <integer>, "topic_name": "<arabic topic up to 5 words>"}\n\n'
            f"## Document excerpt:\n{snippet}"
        )
        system_msg = "You are a classification assistant. Return valid JSON only with keys college_id and topic_name. No extra text."

    try:
        response = llm.chat([
            ChatMessage(role="system", content=system_msg),
            ChatMessage(role="user", content=prompt),
        ], temperature=0)
        raw_content = (response.message.content or "").strip()
        print(f"[classify] Raw classification response: {raw_content}")
        result = json.loads(raw_content)

        if forced_college_id is not None:
            college_id = forced_college_id
            raw_major = result.get("major_id")
            try:
                major_id = int(raw_major) if raw_major is not None else None
            except (TypeError, ValueError):
                major_id = None
        else:
            raw_college = result.get("college_id")
            try:
                college_id = int(raw_college)
            except (TypeError, ValueError):
                college_id = 0
            major_id = None

        topic_name = str(result.get("topic_name") or "").strip()
        if topic_name:
            topic_name = " ".join(topic_name.split()[:5])

        # Upsert topic row so topic_id is always a valid FK
        topic_id = None
        if topic_name:
            t_result = supabase_admin.table("topic").select("topic_id").eq("topic_name", topic_name).execute()
            if t_result.data:
                topic_id = t_result.data[0]["topic_id"]
            else:
                insert_result = supabase_admin.table("topic").insert({"topic_name": topic_name}).execute()
                topic_id = insert_result.data[0]["topic_id"]

        return {"college_id": college_id, "major_id": major_id, "topic_id": topic_id}

    except Exception as e:
        print(f"[classify] Warning: classification failed — {e}")
        return {"college_id": forced_college_id or 0, "major_id": None, "topic_id": None}

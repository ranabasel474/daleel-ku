from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from openai import OpenAI as OpenAIClient
from app import limiter
from config import supabase_admin, OPENAI_API_KEY
from rag.ingest import build_index
from rag.query_engine import search_query
from rag.response import generate_response, handle_gpa_query
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage
from pylatexenc.latex2text import LatexNodes2Text
from utils.sanitize import sanitize_text

#OpenAI client used only to classify the query type
_openai_client = OpenAIClient(api_key=OPENAI_API_KEY)

index = build_index()

session_memories: dict[str, ChatMemoryBuffer] = {}

chat_bp = Blueprint("chat", __name__)  # Chat API routes

MAX_QUERY_LENGTH = 1000

GPA_DISCLAIMER_AR = "هذا تقدير للمعدل لأغراض المرجعية فقط. يرجى التحقق من سجلك الأكاديمي الرسمي."
GPA_DISCLAIMER_EN = "This is an estimated GPA for reference only. Please verify with your official academic record."

_latex_converter = LatexNodes2Text()


def format_gpa_response(answer, query_text):
    answer = _latex_converter.latex_to_text(answer)
    is_arabic = any('؀' <= ch <= 'ۿ' for ch in query_text)
    disclaimer = GPA_DISCLAIMER_AR if is_arabic else GPA_DISCLAIMER_EN
    return f"{answer}\n\n{disclaimer}"

# Validates and sanitizes the student query before processing
def validate_query(text):
    # Reject empty input
    if not text or not text.strip():
        return False, None, "Query can't be empty."

    # Sanitize: strip null bytes, control chars, normalize Unicode
    text = sanitize_text(text)

    if not text:
        return False, None, "Query can't be empty."

    # Reject long input quries
    if len(text) > MAX_QUERY_LENGTH:
        return False, None, f"Query is too long. Maximum allowed length is {MAX_QUERY_LENGTH} characters."

    return True, text, None


# Classifies the query as 'gpa' or 'general'
def detect_query_type(text):
    classification_prompt = (
        "You are a query classifier for a Kuwait University academic chatbot. "
        "Classify the following student query into exactly one of two categories:\n"
        "- gpa       : the student is asking to calculate or estimate their GPA\n"
        "- general   : the student is asking any other academic question\n\n"
        "Reply with one word only: gpa or general. Do not explain."
    )

    try:
        result = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": classification_prompt},
                {"role": "user", "content": text},
            ],
            max_tokens=5,
            temperature=0,
        )
        label = result.choices[0].message.content.strip().lower()
        return "gpa" if label == "gpa" else "general"

    except Exception as e:
        print(f"Warning: detect_query_type failed, defaulting to 'general' — {e}")
        return "general"


# Shared helper — runs GPA or RAG handler and returns a Flask response tuple
def _process_and_respond(query_text, session_id, query_type):
    memory = None
    if session_id:
        if session_id not in session_memories:
            session_memories[session_id] = ChatMemoryBuffer.from_defaults(token_limit=3000)
        memory = session_memories[session_id]

    # Process query based on its type
    if query_type == "gpa":
        result = handle_gpa_query(query_text, memory=memory)
        result["answer"] = format_gpa_response(result["answer"], query_text)
    else:
        search_result = search_query(index, query_text)
        result = generate_response(search_result, query_text, memory=memory)

    # Log the query and response to Supabase
    response_text = result["answer"]
    was_answered = result["was_answered"]
    source_url = result.get("source_url")
    source_name = result.get("source_name")

    #Logging failure must not block the student from receiving their response
    try:
        log_entry = {
            "query_text": query_text,
            "response_text": response_text,
            "was_answered": was_answered,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if session_id:
            log_entry["session_id"] = session_id

        supabase_admin.table("user_query").insert(log_entry).execute()

    except Exception as e:
        print(f"Warning: failed to log query to Supabase — {e}")

    if memory is not None:
        memory.put(ChatMessage(role="user", content=query_text))
        memory.put(ChatMessage(role="assistant", content=response_text))

    # Return the response to the student
    return jsonify({
        "response": response_text,
        "was_answered": was_answered,
        "source_url": source_url,
        "source_name": source_name,
    }), 200


@chat_bp.route("/query", methods=["POST"])  # Query endpoint
@limiter.limit("30 per minute")  # Per-IP rate limit

# Main query handler — kept unchanged for backward compatibility with test.py
def query():
    data = request.get_json()
    query_text = data.get("message", "") if data else ""
    session_id = data.get("session_id") if data else None

    # 1) validate and sanitize query
    is_valid, query_text, error_message = validate_query(query_text)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # 2) Classify query type
    query_type = detect_query_type(query_text)

    # 3) Process and return
    return _process_and_respond(query_text, session_id, query_type)


@chat_bp.route("/query/classify", methods=["POST"])  # Classify-only endpoint
@limiter.limit("30 per minute")  # Per-IP rate limit

# Step 1 of the split flow — validates and classifies only, no RAG or response generation
def query_classify():
    data = request.get_json()
    query_text = data.get("message", "") if data else ""

    # 1) Validate and sanitize query
    is_valid, query_text, error_message = validate_query(query_text)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # 2) Classify and return immediately
    query_type = detect_query_type(query_text)
    return jsonify({"query_type": query_type}), 200


@chat_bp.route("/query/complete", methods=["POST"])  # Completion endpoint
@limiter.limit("30 per minute")  # Per-IP rate limit

# Step 2 of the split flow — skips classification, goes straight to RAG or GPA handler
def query_complete():
    data = request.get_json()
    query_text = data.get("message", "") if data else ""
    session_id = data.get("session_id") if data else None
    query_type = data.get("query_type", "general")

    # 1) Validate and sanitize query
    is_valid, query_text, error_message = validate_query(query_text)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # 2) Guard against unexpected query_type values
    if query_type not in ("gpa", "general"):
        return jsonify({"error": "query_type must be 'gpa' or 'general'."}), 400

    # 3) Process and return
    return _process_and_respond(query_text, session_id, query_type)


#Creates a new session row and returns the session_id
@chat_bp.route("/session", methods=["POST"])
def create_session():
    try:
        result = supabase_admin.table("session").insert({
            "started_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        session_id = result.data[0]["session_id"]
        return jsonify({"session_id": session_id}), 201

    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({"error": "Could not create a new session."}), 500


# 6) Ends a session by setting ended_at
@chat_bp.route("/session/<session_id>", methods=["PATCH"])
def end_session(session_id):
    try:
        supabase_admin.table("session").update({
            "ended_at": datetime.now(timezone.utc).isoformat()
        }).eq("session_id", session_id).execute()

        session_memories.pop(session_id, None)
        return jsonify({"session_id": session_id}), 200
    
    # Raise an error when session_id is invalid or database update fails
    except Exception as e:
        print(f"Error ending session {session_id}: {e}")
        return jsonify({"error": "Could not end the session."}), 500

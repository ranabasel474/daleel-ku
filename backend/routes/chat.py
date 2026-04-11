from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from openai import OpenAI as OpenAIClient  # direct OpenAI client used only for query classification
from app import limiter  # rate limiter instance defined at module level in app.py
from config import supabase_admin, OPENAI_API_KEY
from rag.ingest import build_index
from rag.query_engine import search_query
from rag.response import generate_response, handle_gpa_query

# Used only for query type classification — kept separate from the LlamaIndex llm in config
_openai_client = OpenAIClient(api_key=OPENAI_API_KEY)

index = build_index()

chat_bp = Blueprint("chat", __name__)

MAX_QUERY_LENGTH = 1000  # characters


# Returns (is_valid, error_message) — error_message is None when valid
def validate_query(text):
    if not text or not text.strip():
        return False, "Query cannot be empty."
    if len(text) > MAX_QUERY_LENGTH:
        return False, f"Query is too long. Maximum allowed length is {MAX_QUERY_LENGTH} characters."
    return True, None


# Classifies the query as 'gpa' or 'general' using GPT-4o
def detect_query_type(text):
    classification_prompt = (
        "You are a query classifier for a Kuwait University academic chatbot. "
        "Classify the following student query into exactly one of two categories:\n"
        "- gpa       : the student is asking to calculate or estimate their GPA\n"
        "- general   : the student is asking any other academic question\n\n"
        "Reply with one word only: gpa or general. Do not explain.\n\n"
        f"Query: {text}"
    )

    try:
        result = _openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": classification_prompt}],
            max_tokens=5,   # only one word expected back
            temperature=0,  # deterministic — classification must be consistent
        )
        label = result.choices[0].message.content.strip().lower()
        return "gpa" if label == "gpa" else "general"

    except Exception as e:
        print(f"Warning: detect_query_type failed, defaulting to 'general' — {e}")
        return "general"


# Receives a student question, routes it through RAG or GPA handler, logs it, and returns the response
@chat_bp.route("/query", methods=["POST"])
@limiter.limit("30 per minute")
def query():
    data = request.get_json()
    query_text = data.get("message", "") if data else ""
    session_id = data.get("session_id") if data else None

    is_valid, error_message = validate_query(query_text)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    query_type = detect_query_type(query_text)

    if query_type == "gpa":
        result = handle_gpa_query(query_text)
    else:
        search_result = search_query(index, query_text)
        result = generate_response(search_result, query_text)

    response_text = result["answer"]
    was_answered = result["was_answered"]
    source_url = result.get("source_url")
    source_name = result.get("source_name")

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
        # Logging failure must not block the student from receiving their response
        print(f"Warning: failed to log query to Supabase — {e}")

    return jsonify({
        "response": response_text,
        "was_answered": was_answered,
        "source_url": source_url,
        "source_name": source_name,
    }), 200


# Creates a new session row and returns the session_id
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


# Closes a session by writing the ended_at timestamp
@chat_bp.route("/session/<session_id>", methods=["PATCH"])
def end_session(session_id):
    try:
        supabase_admin.table("session").update({
            "ended_at": datetime.now(timezone.utc).isoformat()
        }).eq("session_id", session_id).execute()

        return jsonify({"session_id": session_id}), 200

    except Exception as e:
        print(f"Error ending session {session_id}: {e}")
        return jsonify({"error": "Could not end the session."}), 500

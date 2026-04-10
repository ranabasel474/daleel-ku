# routes/chat.py
# Handles all student-facing chat routes:
#   POST /api/query   — receives a question, validates it, routes to RAG or GPA,
#                       logs the interaction, and returns the response
#   POST /api/session — creates a new chat session and returns the session_id

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from openai import OpenAI as OpenAIClient

from app import limiter
from config import supabase_admin, OPENAI_API_KEY

# OpenAI client used only for query type classification.
# The same GPT-4o model defined in config.py is used here directly.
_openai_client = OpenAIClient(api_key=OPENAI_API_KEY)

# --- RAG pipeline imports ---
from rag.ingest import build_index
from rag.query_engine import search_query
from rag.response import generate_response, handle_gpa_query

# Build the vector index once at module load so it is reused across requests.
index = build_index()


# -----------------------------------------------------------------------
# Blueprint
# -----------------------------------------------------------------------
chat_bp = Blueprint("chat", __name__)


# -----------------------------------------------------------------------
# InputValidator logic
# Report III / diagrams_description.md:
#   InputValidator.validateQuery(input: String): Boolean
#   Attributes: maxLength (enforces character limit to prevent prompt injection)
# -----------------------------------------------------------------------
MAX_QUERY_LENGTH = 1000  # characters


def validate_query(text):
    """
    Validates the student's query before any processing takes place.

    Implements InputValidator.validateQuery() from the class diagram.
    Two rules are checked:
      1. The query must not be empty or blank.
      2. The query must not exceed MAX_QUERY_LENGTH characters.
         This limit prevents prompt injection attempts (Report III: Input Validation).

    Args:
        text (str): The raw query string received from the frontend.

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
               error_message is None when is_valid is True.
    """
    if not text or not text.strip():
        return False, "Query cannot be empty."
    if len(text) > MAX_QUERY_LENGTH:
        return False, f"Query is too long. Maximum allowed length is {MAX_QUERY_LENGTH} characters."
    return True, None


# -----------------------------------------------------------------------
# QueryProcessor logic
# Report III / diagrams_description.md:
#   QueryProcessor.detectQueryType(text: String): String
#   Returns either "gpa" or "general"
#   Uses GPT-4o classification so Arabic and English are both handled
#   correctly without maintaining a keyword list.
# -----------------------------------------------------------------------
def detect_query_type(text):
    """
    Detects whether the student's query is GPA-related or a general academic question.

    Implements QueryProcessor.detectQueryType() from the class diagram.
    Sends the query to GPT-4o with a strict classification prompt and asks
    it to reply with one word only — "gpa" or "general".
    This works for both Arabic and English input without a keyword list.

    max_tokens=5 keeps the call cheap and fast — we only need one word back.
    If the OpenAI call fails for any reason, the function defaults to "general"
    so the student still receives a response.

    Args:
        text (str): The validated query string.

    Returns:
        str: "gpa"     — if the query is about GPA estimation
             "general" — for all other academic questions
    """
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
            max_tokens=5,
            temperature=0  # deterministic — we want a consistent classification
        )
        label = result.choices[0].message.content.strip().lower()

        # Only accept the two expected labels; treat anything else as "general"
        if label == "gpa":
            return "gpa"
        return "general"

    except Exception as e:
        # If the classification call fails, default to "general" so the student
        # is not left without a response.
        print(f"Warning: detect_query_type failed, defaulting to 'general' — {e}")
        return "general"


# -----------------------------------------------------------------------
# POST /query
# Follows UC02 Submit Query sequence diagram (Report III, pg. 23-24)
# Steps 1-2  : frontend sends query text
# Step  3    : validate input + detect query type
# Steps 4-10 : call RAG pipeline (stubbed until rag/ is implemented)
# Step  11   : log query + response anonymously to Supabase
# Steps 12-13: return response to frontend
# -----------------------------------------------------------------------
@chat_bp.route("/query", methods=["POST"])
@limiter.limit("30 per minute")
def query():
    """
    Receives a student question and returns the chatbot's response.

    This is the main chat endpoint used by the React frontend (UC02).
    Rate limited to 30 requests per minute per IP (Report III: Rate Limiting).

    Expected JSON body:
        {
            "message": "What are the admission requirements?",
            "session_id": "uuid-string"   <-- optional, from POST /session
        }

    Returns:
        200 with { "response": str, "source": str or null, "was_answered": bool }
        400 with { "error": str } if input validation fails
        500 with { "error": str } if an unexpected server error occurs
    """
    data = request.get_json()

    # --- Steps 1-2: Extract fields from the request body ---
    query_text = data.get("message", "") if data else ""
    session_id = data.get("session_id") if data else None

    # --- Step 3a: Validate input (InputValidator logic) ---
    is_valid, error_message = validate_query(query_text)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # --- Step 3b: Detect query type (QueryProcessor logic) ---
    query_type = detect_query_type(query_text)

    # --- Steps 4-10: Call RAG pipeline or GPA handler ---
    if query_type == "gpa":
        # GPA queries go directly to the LLM — no RAG retrieval needed.
        # Report III Backend package: "OpenAI API directly for tasks such as GPA estimation"
        result = handle_gpa_query(query_text)
    else:
        # General academic queries go through the full RAG pipeline.
        # Steps 4-8: search knowledge base → retrieve chunks → generate response
        context = search_query(index, query_text)
        result = generate_response(context, query_text)

    response_text = result["answer"]
    was_answered = result["was_answered"]
    source = None

    # --- Step 11: Log query and response anonymously to Supabase ---
    # Report III (Data Privacy): logs store only query text, response text, and timestamp.
    # No student identity or personal information is recorded.
    try:
        log_entry = {
            "query_text": query_text,
            "response_text": response_text,
            "was_answered": was_answered,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        # Attach session_id only if the frontend provided one
        if session_id:
            log_entry["session_id"] = session_id

        supabase_admin.table("user_query").insert(log_entry).execute()

    except Exception as e:
        # A logging failure must not block the student from receiving their response.
        print(f"Warning: failed to log query to Supabase — {e}")

    # --- Steps 12-13: Return the response to the frontend ---
    return jsonify({
        "response": response_text,
        "source": source,
        "was_answered": was_answered
    }), 200


# -----------------------------------------------------------------------
# POST /session
# Creates a new session row in Supabase and returns the session_id.
# Called by the frontend when the student first opens the chat interface.
# The session_id is then attached to all subsequent /query requests so that
# queries can be grouped by session in the admin Query Logs view.
# Report III database schema: session(session_id, started_at, ended_at)
# -----------------------------------------------------------------------
@chat_bp.route("/session", methods=["POST"])
def create_session():
    """
    Creates a new chat session in the Supabase session table.

    The frontend calls this once when the student opens the chat page.
    The returned session_id must be included in the body of every
    subsequent POST /api/query call so queries are grouped correctly
    in the admin Query Logs interface.

    Returns:
        201 with { "session_id": str }
        500 with { "error": str } if the session could not be created
    """
    try:
        result = supabase_admin.table("session").insert({
            "started_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        session_id = result.data[0]["session_id"]
        return jsonify({"session_id": session_id}), 201

    except Exception as e:
        print(f"Error creating session: {e}")
        return jsonify({"error": "Could not create a new session."}), 500


# -----------------------------------------------------------------------
# PATCH /session/<session_id>
# Closes a session by writing the ended_at timestamp.
# Called by the frontend when the student starts a new chat, closing
# the previous session so the duration is recorded in the database.
# Report III database schema: session(session_id, started_at, ended_at)
# -----------------------------------------------------------------------
@chat_bp.route("/session/<session_id>", methods=["PATCH"])
def end_session(session_id):
    """
    Sets ended_at on an existing session row, marking it as closed.

    The frontend calls this before creating a new session (i.e., when the
    student clicks "New Chat"). Without this call, ended_at remains NULL
    and session duration cannot be calculated in the admin Query Logs view.

    Args (URL):
        session_id (str): UUID of the session to close.

    Returns:
        200 with { "session_id": str }
        500 with { "error": str } if the update fails
    """
    try:
        supabase_admin.table("session").update({
            "ended_at": datetime.now(timezone.utc).isoformat()
        }).eq("session_id", session_id).execute()

        return jsonify({"session_id": session_id}), 200

    except Exception as e:
        print(f"Error ending session {session_id}: {e}")
        return jsonify({"error": "Could not end the session."}), 500

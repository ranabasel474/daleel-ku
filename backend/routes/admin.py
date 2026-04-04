from flask import Blueprint, request, jsonify
from config import supabase, supabase_admin
from auth.jwt import require_auth

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["POST"])
def login():
    """Authenticate an admin user via Supabase Auth.

    Expects a JSON body with 'email' and 'password'. Calls
    supabase.auth.sign_in_with_password() and returns the JWT
    access token on success.

    Returns:
        200: {"access_token": <token>}
        400: {"error": "email and password are required"} if fields missing
        401: {"error": "Invalid credentials"} if login fails
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        access_token = response.session.access_token
        return jsonify({"access_token": access_token}), 200
    except Exception:
        return jsonify({"error": "Invalid credentials"}), 401


@admin_bp.route("/documents", methods=["GET"])
@require_auth
def get_documents():
    """Return all documents from the document table.

    Protected route — requires a valid Bearer token in the
    Authorization header.

    Returns:
        200: {"documents": [<document>, ...]}
        500: {"error": <message>} if the database call fails
    """
    try:
        response = supabase_admin.table("document").select("*").execute()
        return jsonify({"documents": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/documents", methods=["POST"])
@require_auth
def add_document():
    """Add a new document record to the document table.

    Protected route — requires a valid Bearer token in the
    Authorization header. Expects a JSON body with the document fields.

    Returns:
        201: {"document": <inserted record>}
        400: {"error": "Request body is required"} if body is empty
        500: {"error": <message>} if the database call fails
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        response = supabase_admin.table("document").insert(data).execute()
        return jsonify({"document": response.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/documents/<doc_id>", methods=["PUT"])
@require_auth
def update_document(doc_id):
    """Update an existing document record by ID.

    Protected route — requires a valid Bearer token in the
    Authorization header. Expects a JSON body with the fields to update.

    Args:
        doc_id: The integer primary key of the document to update.

    Returns:
        200: {"document": <updated record>}
        400: {"error": "Request body is required"} if body is empty
        500: {"error": <message>} if the database call fails
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        response = supabase_admin.table("document").update(data).eq("document_id", doc_id).execute()
        return jsonify({"document": response.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/documents/<doc_id>", methods=["DELETE"])
@require_auth
def delete_document(doc_id):
    """Delete a document record by ID.

    Protected route — requires a valid Bearer token in the
    Authorization header.

    Args:
        doc_id: The integer primary key of the document to delete.

    Returns:
        200: {"message": "Document deleted"}
        500: {"error": <message>} if the database call fails
    """
    try:
        supabase_admin.table("document").delete().eq("document_id", doc_id).execute()
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/queries", methods=["GET"])
@require_auth
def get_queries():
    """Return all user_query rows ordered by created_at descending.

    Protected route — requires a valid Bearer token in the
    Authorization header.

    Returns:
        200: {"queries": [<query>, ...]}
        500: {"error": <message>} if the database call fails
    """
    try:
        response = (
            supabase_admin.table("user_query")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify({"queries": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

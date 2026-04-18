from flask import Blueprint, request, jsonify
from config import supabase, supabase_admin
from auth.jwt import require_auth

admin_bp = Blueprint("admin", __name__)

#Authenticates an admin via Supabase Auth and returns a JWT access token
@admin_bp.route("/login", methods=["POST"])
def login():
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

#Returns all documents from the document table
@admin_bp.route("/documents", methods=["GET"])
@require_auth
def get_documents():
    try:
        response = supabase_admin.table("document").select("*").execute()
        return jsonify({"documents": response.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Inserts a new document record
@admin_bp.route("/documents", methods=["POST"])
@require_auth
def add_document():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        response = supabase_admin.table("document").insert(data).execute()
        return jsonify({"document": response.data[0]}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Updates an existing document record by ID
@admin_bp.route("/documents/<doc_id>", methods=["PUT"])
@require_auth
def update_document(doc_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    try:
        response = supabase_admin.table("document").update(data).eq("document_id", doc_id).execute()
        return jsonify({"document": response.data[0]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Deletes an existing document record by ID
@admin_bp.route("/documents/<doc_id>", methods=["DELETE"])
@require_auth
def delete_document(doc_id):
    try:
        supabase_admin.table("document").delete().eq("document_id", doc_id).execute()
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#Returns all user_query rows ordered by created_at descending
@admin_bp.route("/queries", methods=["GET"])
@require_auth
def get_queries():
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

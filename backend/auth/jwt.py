from functools import wraps
from flask import request, jsonify
from config import supabase

# Validates the Bearer token with Supabase Auth and returns the user object
def verify_token(token: str) -> dict:
    response = supabase.auth.get_user(token)
    return response.user

# Route decorator that rejects requests without a valid Bearer token
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]

        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

        # Attach verified user to request so route handlers can access it
        request.admin_payload = payload
        return f(*args, **kwargs)

    return decorated

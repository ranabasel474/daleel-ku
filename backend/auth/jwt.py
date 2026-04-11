from functools import wraps  # preserves the original function's name and metadata in decorators
from flask import request, jsonify
from config import supabase


# Validates a JWT token via Supabase Auth and returns the user object
def verify_token(token: str) -> dict:
    response = supabase.auth.get_user(token)
    return response.user


# Flask decorator that protects admin routes — extracts and verifies the Bearer token
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]  # strip "Bearer " prefix to get the raw token

        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

        request.admin_payload = payload  # makes the verified user available to the route handler
        return f(*args, **kwargs)

    return decorated

from functools import wraps   # decorator metadata preservation
from flask import request, jsonify  # request parsing, JSON responses
from config import supabase  # Supabase client


# Verifies a JWT token via Supabase Auth and returns the user object
def verify_token(token: str) -> dict:
    response = supabase.auth.get_user(token)
    return response.user


# Flask decorator that protects admin routes
def require_auth(f):
    @wraps(f)
    # Extracts the Bearer token, verifies it, and attaches the user to the request
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401  # missing or malformed header

        # Strip "Bearer " prefix to get the raw token
        token = auth_header[len("Bearer "):]

        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401  # invalid or expired token

        # Make the verified user available to the route handler
        request.admin_payload = payload
        return f(*args, **kwargs)

    return decorated
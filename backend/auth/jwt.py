from functools import wraps
from flask import request, jsonify
from config import supabase


def verify_token(token: str) -> dict:
    """Validate a JWT token issued by Supabase Auth.

    Calls the Supabase Auth API to verify the token and retrieve the
    associated user. Raises an exception if the token is invalid,
    expired, or malformed.

    Args:
        token: The raw JWT string to verify.

    Returns:
        The user object returned by Supabase as a dictionary.

    Raises:
        Exception: If token verification fails for any reason.
    """
    response = supabase.auth.get_user(token)
    return response.user


def require_auth(f):
    """Flask decorator that protects admin routes with JWT authentication.

    Reads the Authorization header, expects a Bearer token, calls
    verify_token() to validate it via Supabase Auth, and attaches the
    returned user object to the request as request.admin_payload.
    Returns a 401 JSON response if the header is missing, malformed,
    or the token is invalid.

    Usage:
        @admin_bp.route("/some-route")
        @require_auth
        def some_route():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        """Inner wrapper that performs the auth check before calling the route."""
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]

        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

        request.admin_payload = payload
        return f(*args, **kwargs)

    return decorated

import jwt
from functools import wraps
from flask import request, jsonify
from config import SUPABASE_JWT_SECRET, JWT_ALGORITHM


def verify_token(token: str) -> dict:
    """Validate a JWT token issued by Supabase Auth.

    Decodes and verifies the token signature using SUPABASE_JWT_SECRET
    and the configured JWT_ALGORITHM. Raises an exception if the token
    is invalid, expired, or malformed.

    Args:
        token: The raw JWT string to verify.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidTokenError: If the token is invalid for any other reason.
    """
    return jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=[JWT_ALGORITHM])


def require_auth(f):
    """Flask decorator that protects admin routes with JWT authentication.

    Reads the Authorization header, expects a Bearer token, calls
    verify_token() to validate it, and attaches the decoded payload to
    the request as request.admin_payload. Returns a 401 JSON response if
    the header is missing, malformed, expired, or invalid.

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
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401

        request.admin_payload = payload
        return f(*args, **kwargs)

    return decorated

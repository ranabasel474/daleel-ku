from functools import wraps
from flask import request, jsonify
from config import supabase

#Checks the JWT with Supabase and returns the user info
def verify_token(token: str) -> dict:
    response = supabase.auth.get_user(token)
    return response.user

#Protects a route and allows only requests with a valid Bearer token
def require_auth(f):
    @wraps(f)
    #Reads the token from the Authorization header and validates it
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        #Remove the Bearer prefix and keep only the token
        token = auth_header[len("Bearer "):]

        try:
            payload = verify_token(token)
        except Exception as e:
            return jsonify({"error": f"Token verification failed: {str(e)}"}), 401

        #Save the verified user data for the route handler
        request.admin_payload = payload
        return f(*args, **kwargs)

    return decorated
# app.py
# Main entry point for the Daleel KU backend.
# Creates the Flask app, registers route blueprints,
# and applies CORS and rate limiting as defined in Report III security strategies.

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Rate Limiter (module-level) ---
# Must be defined here, before any blueprint is imported.
# routes/chat.py does "from app import limiter" — if blueprints were imported
# above this line, limiter would not exist yet and Python would raise ImportError.
# Report III: rate limiting is applied to the public chat endpoint only.
limiter = Limiter(get_remote_address)


def create_app():
    """
    Application factory function.
    Initializes Flask app with all required extensions and blueprints.
    """
    app = Flask(__name__)

    # --- CORS ---
    # Restricts cross-origin requests to the React frontend origin only.
    # Report III: controlled frontend-backend communication channel.
    CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

    # --- Rate Limiting ---
    # Attached to the app here; no default limit is set globally.
    # The 30/min limit is applied only on the public chat endpoint in routes/chat.py.
    # Report III Security Strategies — Rate Limiting section.
    limiter.init_app(app)

    # --- Route Blueprints ---
    # Imported here (inside the factory) so that by the time these modules load
    # and execute "from app import limiter", app.py is already fully initialized
    # and limiter is defined. Importing them at the top of app.py would trigger
    # the circular import before limiter exists.
    # chat_bp   → handles student queries (/api/query, /api/gpa, /api/session)
    # admin_bp  → handles admin panel (/api/admin/login, /api/admin/documents, etc.)
    from routes.chat import chat_bp
    from routes.admin import admin_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # --- Health Check ---
    @app.route("/")
    def health_check():
        """
        Health check endpoint.
        Used to verify the backend is running before connecting the frontend.
        """
        return jsonify({
            "status": "running",
            "system": "Daleel KU - Academic Chatbot for Kuwait University"
        }), 200

    # --- Error Handlers ---
    @app.errorhandler(404)
    def not_found(e):
        """Returns a JSON 404 error instead of HTML — consistent with API design."""
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """Returns a friendly message when rate limit is hit."""
        return jsonify({
            "error": "Too many requests. Please wait a moment before trying again."
        }), 429

    @app.errorhandler(500)
    def internal_error(e):
        """Returns a JSON 500 error for unexpected server issues."""
        return jsonify({"error": "An internal server error occurred."}), 500

    return app


# --- Run ---
if __name__ == "__main__":
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000)

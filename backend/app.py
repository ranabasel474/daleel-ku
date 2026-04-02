# app.py
# Main entry point for the Daleel KU backend.
# Creates the Flask app, registers route blueprints,
# and applies CORS and rate limiting as defined in Report III security strategies.

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes.chat import chat_bp
from routes.admin import admin_bp

def create_app():
    """
    Application factory function.
    Initializes Flask app with all required extensions and blueprints.
    """
    app = Flask(__name__)

    # --- CORS ---
    # Allows the React frontend to communicate with this backend.
    # As specified in Report III Communications Interfaces section.
    CORS(app)

    # --- Rate Limiting ---
    # Protects the public chat endpoint from abuse and controls OpenAI API costs.
    # Applies to all routes by default — 30 requests per minute per IP.
    # As specified in Report III Security Strategies — Rate Limiting section.
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["30 per minute"]
    )

    # --- Route Blueprints ---
    # chat_bp   → handles student queries (/api/query, /api/session)
    # admin_bp  → handles admin panel (/api/admin/login, /api/admin/documents, etc.)
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
    app.run(debug=True, port=5000)
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Shared rate limiter instance — initialized here so routes/chat.py can import it before the app is created
limiter = Limiter(get_remote_address)

# Application factory — initializes CORS, rate limiter, blueprints, and error handlers
def create_app():
    app = Flask(__name__)

    CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

    limiter.init_app(app)

    # Import blueprints after limiter setup
    from routes.chat import chat_bp
    from routes.admin import admin_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    # Returns server status and system name; used as the deployment health probe
    @app.route("/")
    def health_check():
        return jsonify({
            "status": "running",
            "system": "Daleel KU - Academic Chatbot for Kuwait University"
        }), 200

    # Returns a JSON error body for any route not matched by a blueprint
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    # Returns a JSON 429 body when a client exceeds the per-IP request cap
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            "error": "Too many requests. Please wait a moment before trying again."
        }), 429

    # Returns a JSON 500 body for any unhandled exception
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "An internal server error occurred."}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000)

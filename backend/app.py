import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address  # identifies clients by IP for rate limiting

# Must be defined at module level before any blueprint is imported
# routes/chat.py does "from app import limiter", so limiter must exist first
limiter = Limiter(get_remote_address)


# Creates and configures the Flask app with extensions and blueprints
def create_app():
    app = Flask(__name__)

    CORS(app, origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")])

    limiter.init_app(app)

    # Imported inside the factory to avoid circular imports — limiter must exist before these load
    from routes.chat import chat_bp
    from routes.admin import admin_bp

    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.route("/")
    def health_check():
        return jsonify({
            "status": "running",
            "system": "Daleel KU - Academic Chatbot for Kuwait University"
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            "error": "Too many requests. Please wait a moment before trying again."
        }), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "An internal server error occurred."}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true", port=5000)

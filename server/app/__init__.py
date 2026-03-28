import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour", "60 per minute"])


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Neon DB
    from . import db
    db.init_db(app.config["DATABASE_URL"])

    # Seed solutions if needed
    from .services import solutions_store
    solutions_store._ensure_seeded()

    allowed_origins = [
        os.getenv("FRONTEND_ORIGIN", "https://customerstalking.web.app"),
        "https://customerstalking.web.app",
        "https://customerstalking.firebaseapp.com",
        "http://localhost:4200",
    ]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    limiter.init_app(app)

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

    from .routes.auth import auth_bp
    from .routes.ussd import ussd_bp
    from .routes.sessions import sessions_bp
    from .routes.sms import sms_bp
    from .routes.voice import voice_bp
    from .routes.solutions import solutions_bp

    limiter.limit("5 per minute")(auth_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(ussd_bp)
    app.register_blueprint(sessions_bp, url_prefix="/api")
    app.register_blueprint(sms_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(solutions_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "customers-talking-server"}

    @app.get("/debug/config")
    def debug_config():
        """Temporary: show which config keys are set (not values)."""
        keys = ["DIALOGFLOW_PROJECT_ID", "DIALOGFLOW_AGENT_ID", "DIALOGFLOW_LOCATION",
                "GOOGLE_SERVICE_ACCOUNT_EMAIL", "GOOGLE_PRIVATE_KEY", "GOOGLE_PRIVATE_KEY_ID",
                "AT_USERNAME", "AT_API_KEY", "DATABASE_URL"]
        return {k: bool(app.config.get(k)) for k in keys}

    @app.get("/debug/dialogflow")
    def debug_dialogflow():
        """Temporary: test Dialogflow CX connection via dialogflow_service.detect_intent.

        This uses the higher-level wrapper which always returns a serializable dict
        (falls back gracefully) to avoid returning raw protobuf/gRPC objects.
        """
        from .services.dialogflow_service import detect_intent
        try:
            result = detect_intent("hello", session_id="debug-test-session", channel="debug")
            # result is a dict with keys: text, intent_name, is_handoff, source
            return {"status": "ok", "dialogflow": result}
        except Exception as e:
            # As a last resort, return stringified error
            import traceback
            return {"status": "error", "error": str(e), "trace": traceback.format_exc()}, 500

    return app

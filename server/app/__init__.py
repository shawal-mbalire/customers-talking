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
        """Temporary: test Dialogflow CX connection and return raw error if any."""
        import traceback
        from .services.dialogflow_service import _get_credentials, _build_session_path
        from google.cloud.dialogflowcx_v3beta1 import SessionsClient
        from google.cloud.dialogflowcx_v3beta1.types import DetectIntentRequest, QueryInput, TextInput
        try:
            creds = _get_credentials()
            location = app.config["DIALOGFLOW_LOCATION"]
            client = SessionsClient(
                credentials=creds,
                client_options={"api_endpoint": f"{location}-dialogflow.googleapis.com"},
            )
            session_path = _build_session_path(client, "debug-test-session")
            req = DetectIntentRequest(
                session=session_path,
                query_input=QueryInput(
                    text=TextInput(text="hello"),
                    language_code=app.config["DIALOGFLOW_LANGUAGE_CODE"],
                ),
            )
            response = client.detect_intent(request=req)
            messages = [m.text.text for m in response.query_result.response_messages if m.text.text]
            intent = getattr(response.query_result.intent, "display_name", "unknown")
            return {"status": "ok", "intent": intent, "messages": messages}
        except Exception as e:
            return {"status": "error", "error": str(e), "trace": traceback.format_exc()}, 500

    return app

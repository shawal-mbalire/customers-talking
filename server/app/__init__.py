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

    frontend_origin = os.getenv("FRONTEND_ORIGIN", "https://customerstalking.web.app")
    CORS(app, resources={r"/api/*": {"origins": frontend_origin}}, supports_credentials=True)

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

    return app

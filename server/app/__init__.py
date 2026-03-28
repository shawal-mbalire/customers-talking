import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per hour", "60 per minute"])


def create_app(config_class=Config) -> Flask:
    # static_folder points to the Angular build copied in by Docker
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    app = Flask(__name__, static_folder=static_dir, static_url_path="")
    app.config.from_object(config_class)

    # Initialize Neon DB
    from . import db
    db.init_db(app.config["DATABASE_URL"])

    # Seed solutions if needed
    from .services import solutions_store
    solutions_store._ensure_seeded()

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

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

    @app.route("/", defaults={"spa_path": ""})
    @app.route("/<path:spa_path>")
    def serve_angular(spa_path):
        """Serve Angular SPA: static assets by name, index.html for all routes."""
        full = os.path.join(app.static_folder, spa_path)
        if spa_path and os.path.exists(full):
            return send_from_directory(app.static_folder, spa_path)
        return send_from_directory(app.static_folder, "index.html")

    return app

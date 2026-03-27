from flask import Flask
from flask_cors import CORS
from .config import Config


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from .routes.ussd import ussd_bp
    from .routes.sessions import sessions_bp

    app.register_blueprint(ussd_bp)
    app.register_blueprint(sessions_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "customers-talking-server"}

    return app

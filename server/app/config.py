import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Africa's Talking
    AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
    AT_API_KEY = os.getenv("AT_API_KEY", "")

    # Dialogflow CX
    DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", "")
    DIALOGFLOW_LOCATION = os.getenv("DIALOGFLOW_LOCATION", "global")
    DIALOGFLOW_AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID", "")
    DIALOGFLOW_LANGUAGE_CODE = os.getenv("DIALOGFLOW_LANGUAGE_CODE", "en")

    # Base URL (used in Voice XML callbacks)
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

    # Neon Database
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Neon Auth (Better Auth)
    NEON_AUTH_BASE_URL = os.getenv("NEON_AUTH_BASE_URL", "")
    _jwks = os.getenv("NEON_AUTH_JWKS_URL", "")
    NEON_AUTH_JWKS_URL = _jwks if _jwks else f"{os.getenv('NEON_AUTH_BASE_URL', '').rstrip('/')}/api/auth/jwks"

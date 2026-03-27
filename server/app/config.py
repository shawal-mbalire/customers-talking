import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

    # Africa's Talking
    AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
    AT_API_KEY = os.getenv("AT_API_KEY", "")

    # Dialogflow CX
    DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", "")
    DIALOGFLOW_LOCATION = os.getenv("DIALOGFLOW_LOCATION", "global")
    DIALOGFLOW_AGENT_ID = os.getenv("DIALOGFLOW_AGENT_ID", "")
    DIALOGFLOW_LANGUAGE_CODE = os.getenv("DIALOGFLOW_LANGUAGE_CODE", "en")

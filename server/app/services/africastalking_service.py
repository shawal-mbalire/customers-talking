"""Africa's Talking SMS helper."""
import africastalking
from flask import current_app


def _get_sms():
    africastalking.initialize(
        current_app.config["AT_USERNAME"],
        current_app.config["AT_API_KEY"],
    )
    return africastalking.SMS


def send_handoff_sms(phone_number: str) -> dict:
    """Notify the customer via SMS that a human agent will follow up."""
    sms = _get_sms()
    message = (
        "Hello! A customer care specialist has been assigned to your case "
        "and will contact you shortly. Thank you for your patience."
    )
    response = sms.send(message, [phone_number])
    return response

"""
In-memory human queue. Delegates to session_store internally.
"""
from ..models.session import EscalatedSession
from . import session_store


def enqueue(session: EscalatedSession) -> None:
    """Mark a session as escalated in the session store."""
    existing = session_store.find_by_session_id(session.session_id)
    if existing:
        existing.status = "escalated"
        existing.reason = session.reason
        existing.last_intent = session.last_intent
        session_store.update(existing)
    else:
        # Create a new unified session for this escalation
        unified = session_store.get_or_create(
            session.phone_number, "ussd", session.session_id
        )
        unified.status = "escalated"
        unified.reason = session.reason
        unified.last_intent = session.last_intent
        session_store.update(unified)


def get_all() -> list[dict]:
    """Return all escalated sessions."""
    return session_store.get_by_status("escalated")


def remove(session_id: str) -> bool:
    """Resolve a session. Returns True if found."""
    return session_store.resolve(session_id)

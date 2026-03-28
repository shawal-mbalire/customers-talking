"""In-memory store for UnifiedSession objects."""
from datetime import datetime, timezone
from ..models.session import UnifiedSession

_sessions: dict[str, UnifiedSession] = {}  # keyed by session_id
_phone_index: dict[str, str] = {}  # phone_number -> session_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create(phone_number: str, channel: str, session_id: str) -> UnifiedSession:
    """Look up by phone_number for cross-channel correlation; create if not found."""
    existing_id = _phone_index.get(phone_number)
    if existing_id and existing_id in _sessions:
        session = _sessions[existing_id]
        # Update channel if it changed
        session.channel = channel
        session.updated_at = _now()
        return session

    session = UnifiedSession(
        session_id=session_id,
        phone_number=phone_number,
        channel=channel,
    )
    _sessions[session_id] = session
    _phone_index[phone_number] = session_id
    return session


def update(session: UnifiedSession) -> None:
    """Save back the session (updates timestamp)."""
    session.updated_at = _now()
    _sessions[session.session_id] = session
    _phone_index[session.phone_number] = session.session_id


def get_all() -> list[dict]:
    return [s.to_dict() for s in _sessions.values()]


def get_by_status(status: str) -> list[dict]:
    return [s.to_dict() for s in _sessions.values() if s.status == status]


def get_by_channel(channel: str) -> list[dict]:
    return [s.to_dict() for s in _sessions.values() if s.channel == channel]


def get_filtered(status: str | None = None, channel: str | None = None) -> list[dict]:
    sessions = list(_sessions.values())
    if status:
        sessions = [s for s in sessions if s.status == status]
    if channel:
        sessions = [s for s in sessions if s.channel == channel]
    return [s.to_dict() for s in sessions]


def resolve(session_id: str) -> bool:
    session = _sessions.get(session_id)
    if not session:
        return False
    session.status = "resolved"
    session.updated_at = _now()
    return True


def find_by_session_id(session_id: str) -> UnifiedSession | None:
    return _sessions.get(session_id)

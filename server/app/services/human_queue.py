"""
In-memory human queue. Replace with a database (Redis/Postgres)
in production by swapping out these two functions.
"""
from ..models.session import EscalatedSession

_queue: list[EscalatedSession] = []


def enqueue(session: EscalatedSession) -> None:
    """Add an escalated session to the human queue."""
    _queue.append(session)


def get_all() -> list[dict]:
    """Return all queued sessions as JSON-serialisable dicts."""
    return [s.to_dict() for s in _queue]


def remove(session_id: str) -> bool:
    """Remove a resolved session from the queue. Returns True if found."""
    global _queue
    before = len(_queue)
    _queue = [s for s in _queue if s.session_id != session_id]
    return len(_queue) < before

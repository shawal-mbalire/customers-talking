"""PostgreSQL-backed store for UnifiedSession objects."""
from datetime import datetime

from psycopg2.extras import Json

from ..db import get_cursor
from ..models.session import UnifiedSession


def _row_to_session(row: dict) -> UnifiedSession:
    def _iso(v) -> str:
        return v.isoformat() if isinstance(v, datetime) else str(v)

    return UnifiedSession(
        session_id=row["session_id"],
        phone_number=row["phone_number"],
        channel=row["channel"],
        status=row["status"],
        last_intent=row["last_intent"],
        last_message=row["last_message"],
        agent_reply=row["agent_reply"],
        reason=row["reason"],
        messages=list(row["messages"] or []),
        awaiting_satisfaction=bool(row["awaiting_satisfaction"]),
        created_at=_iso(row["created_at"]),
        updated_at=_iso(row["updated_at"]),
    )


def get_or_create(phone_number: str, channel: str, session_id: str) -> UnifiedSession:
    """Look up by phone_number for cross-channel correlation; create if not found."""
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sessions WHERE phone_number = %s", (phone_number,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE sessions SET channel = %s, updated_at = NOW() WHERE session_id = %s RETURNING *",
                (channel, row["session_id"]),
            )
            return _row_to_session(cur.fetchone())
        cur.execute(
            "INSERT INTO sessions (session_id, phone_number, channel) VALUES (%s, %s, %s) RETURNING *",
            (session_id, phone_number, channel),
        )
        return _row_to_session(cur.fetchone())


def update(session: UnifiedSession) -> None:
    """Save back the session."""
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE sessions SET
                channel = %s, status = %s, last_intent = %s,
                last_message = %s, agent_reply = %s, reason = %s,
                messages = %s, awaiting_satisfaction = %s,
                updated_at = NOW()
            WHERE session_id = %s
            """,
            (
                session.channel, session.status, session.last_intent,
                session.last_message, session.agent_reply, session.reason,
                Json(session.messages), session.awaiting_satisfaction,
                session.session_id,
            ),
        )


def get_all() -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sessions ORDER BY updated_at DESC")
        return [_row_to_session(r).to_dict() for r in cur.fetchall()]


def get_by_status(status: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sessions WHERE status = %s ORDER BY updated_at DESC", (status,))
        return [_row_to_session(r).to_dict() for r in cur.fetchall()]


def get_by_channel(channel: str) -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sessions WHERE channel = %s ORDER BY updated_at DESC", (channel,))
        return [_row_to_session(r).to_dict() for r in cur.fetchall()]


def get_filtered(status: str | None = None, channel: str | None = None) -> list[dict]:
    conditions, params = [], []
    if status:
        conditions.append("status = %s")
        params.append(status)
    if channel:
        conditions.append("channel = %s")
        params.append(channel)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_cursor() as cur:
        cur.execute(f"SELECT * FROM sessions {where} ORDER BY updated_at DESC", params)
        return [_row_to_session(r).to_dict() for r in cur.fetchall()]


def resolve(session_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE sessions SET status = 'resolved', updated_at = NOW() WHERE session_id = %s RETURNING session_id",
            (session_id,),
        )
        return cur.fetchone() is not None


def find_by_session_id(session_id: str) -> UnifiedSession | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
        row = cur.fetchone()
        return _row_to_session(row) if row else None

"""PostgreSQL-backed CRUD store for predefined Solution answers."""
import uuid
from datetime import datetime

from psycopg2.extras import Json

from ..db import get_cursor
from ..models.session import Solution


def _row_to_solution(row: dict) -> Solution:
    def _iso(v) -> str:
        return v.isoformat() if isinstance(v, datetime) else str(v)

    return Solution(
        id=row["id"],
        question=row["question"],
        answer=row["answer"],
        intent_name=row["intent_name"],
        trigger_phrases=list(row["trigger_phrases"] or []),
        channels=list(row["channels"] or ["all"]),
        active=bool(row["active"]),
        created_at=_iso(row["created_at"]),
    )


def _seed() -> None:
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS cnt FROM solutions")
        if cur.fetchone()["cnt"] > 0:
            return
        samples = [
            ("How do I check my balance?", "Dial *123# to check your account balance instantly.", "check_balance", ["check balance", "my balance", "account balance", "balance"], ["all"]),
            ("What are your working hours?", "We are open Monday to Friday, 8 AM – 6 PM EAT.", "working_hours", ["working hours", "opening hours", "office hours", "open"], ["all"]),
            ("How do I reset my PIN?", "Send RESET to 20880 and follow the instructions sent to you.", "reset_pin", ["reset pin", "forgot pin", "change pin", "pin reset"], ["all"]),
            ("How do I make a payment?", "Dial *456# and select 'Pay Bill', then enter the biller code provided.", "make_payment", ["make payment", "pay bill", "payment", "pay"], ["ussd", "sms"]),
            ("What is the SMS shortcode?", "Our SMS shortcode is 20880. Text your question and we'll reply instantly.", "sms_shortcode", ["sms shortcode", "shortcode", "text number", "sms number"], ["all"]),
        ]
        for q, a, intent, phrases, channels in samples:
            cur.execute(
                "INSERT INTO solutions (id, question, answer, intent_name, trigger_phrases, channels) VALUES (%s, %s, %s, %s, %s, %s)",
                (str(uuid.uuid4()), q, a, intent, Json(phrases), Json(channels)),
            )


def _ensure_seeded() -> None:
    _seed()


def get_all() -> list[dict]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM solutions ORDER BY created_at ASC")
        return [_row_to_solution(r).to_dict() for r in cur.fetchall()]


def get_active() -> list[Solution]:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM solutions WHERE active = TRUE ORDER BY created_at ASC")
        return [_row_to_solution(r) for r in cur.fetchall()]


def get_by_id(solution_id: str) -> Solution | None:
    with get_cursor() as cur:
        cur.execute("SELECT * FROM solutions WHERE id = %s", (solution_id,))
        row = cur.fetchone()
        return _row_to_solution(row) if row else None


def create(data: dict) -> Solution:
    s_id = str(uuid.uuid4())
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO solutions (id, question, answer, intent_name, trigger_phrases, channels, active) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *",
            (
                s_id, data.get("question", ""), data.get("answer", ""),
                data.get("intentName", ""),
                Json(data.get("triggerPhrases", [])),
                Json(data.get("channels", ["all"])),
                data.get("active", True),
            ),
        )
        return _row_to_solution(cur.fetchone())


def update(solution_id: str, data: dict) -> Solution | None:
    sol = get_by_id(solution_id)
    if not sol:
        return None
    if "question" in data:
        sol.question = data["question"]
    if "answer" in data:
        sol.answer = data["answer"]
    if "intentName" in data:
        sol.intent_name = data["intentName"]
    if "triggerPhrases" in data:
        sol.trigger_phrases = data["triggerPhrases"]
    if "channels" in data:
        sol.channels = data["channels"]
    if "active" in data:
        sol.active = data["active"]
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE solutions SET
                question = %s, answer = %s, intent_name = %s,
                trigger_phrases = %s, channels = %s, active = %s
            WHERE id = %s RETURNING *
            """,
            (sol.question, sol.answer, sol.intent_name,
             Json(sol.trigger_phrases), Json(sol.channels), sol.active, solution_id),
        )
        return _row_to_solution(cur.fetchone())


def delete(solution_id: str) -> bool:
    with get_cursor() as cur:
        cur.execute("DELETE FROM solutions WHERE id = %s RETURNING id", (solution_id,))
        return cur.fetchone() is not None


def find_match(text: str, channel: str) -> Solution | None:
    """Find first active solution matching text via trigger_phrases (case-insensitive substring)."""
    text_lower = text.lower()
    for solution in get_active():
        if "all" not in solution.channels and channel not in solution.channels:
            continue
        for phrase in solution.trigger_phrases:
            if phrase.lower() in text_lower:
                return solution
    return None

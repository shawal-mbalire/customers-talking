"""PostgreSQL connection pool and schema initialization for Neon."""
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None


def init_db(database_url: str) -> None:
    global _pool
    _pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=database_url)
    _create_tables()


@contextmanager
def get_cursor():
    assert _pool is not None, "Database not initialized — call init_db() first"
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def _create_tables() -> None:
    with get_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id           TEXT PRIMARY KEY,
                phone_number         TEXT UNIQUE NOT NULL,
                channel              TEXT NOT NULL,
                status               TEXT NOT NULL DEFAULT 'active',
                last_intent          TEXT NOT NULL DEFAULT 'unknown',
                last_message         TEXT NOT NULL DEFAULT '',
                agent_reply          TEXT NOT NULL DEFAULT '',
                reason               TEXT NOT NULL DEFAULT '',
                messages             JSONB NOT NULL DEFAULT '[]',
                awaiting_satisfaction BOOLEAN NOT NULL DEFAULT FALSE,
                created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS solutions (
                id              TEXT PRIMARY KEY,
                question        TEXT NOT NULL,
                answer          TEXT NOT NULL,
                intent_name     TEXT NOT NULL DEFAULT '',
                trigger_phrases JSONB NOT NULL DEFAULT '[]',
                channels        JSONB NOT NULL DEFAULT '["all"]',
                active          BOOLEAN NOT NULL DEFAULT TRUE,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

"""
PostgreSQL storage for MCP Commands — tracking AI command usage.
"""

import json
import os
from datetime import datetime, date
from typing import Optional

import psycopg2
import psycopg2.extras


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://mcp_commands:mcp_commands@localhost:5432/mcp_commands",
)


def get_connection() -> psycopg2.extensions.connection:
    """Open PostgreSQL connection and ensure tables exist."""
    conn = psycopg2.connect(DATABASE_URL)
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: psycopg2.extensions.connection):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS command_log (
                id          SERIAL PRIMARY KEY,
                command     TEXT        NOT NULL,
                category    TEXT,
                context     TEXT,
                extra       JSONB,
                used_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_command     ON command_log (command);
            CREATE INDEX IF NOT EXISTS idx_used_at     ON command_log (used_at);
            CREATE INDEX IF NOT EXISTS idx_category    ON command_log (category);
        """)
    conn.commit()


# ─────────────────────────────────────────────
# Write
# ─────────────────────────────────────────────

def log_command(
    command: str,
    category: Optional[str] = None,
    context: Optional[str] = None,
    extra: Optional[dict] = None,
) -> int:
    """Insert one command-usage record. Returns the new row id."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO command_log (command, category, context, extra, used_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                command,
                category,
                context,
                json.dumps(extra) if extra else None,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        row_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return row_id


# ─────────────────────────────────────────────
# Read
# ─────────────────────────────────────────────

def get_history(
    limit: int = 50,
    command: Optional[str] = None,
    category: Optional[str] = None,
) -> list[dict]:
    """Return recent command-usage records (newest first)."""
    conn = get_connection()

    clauses = []
    params: list = []

    if command:
        clauses.append("command ILIKE %s")
        params.append(f"%{command}%")
    if category:
        clauses.append("category = %s")
        params.append(category)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(limit)

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            f"SELECT * FROM command_log {where} ORDER BY used_at DESC LIMIT %s",
            params,
        )
        rows = cur.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_stats(top_n: int = 10) -> dict:
    """Return usage statistics."""
    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM command_log")
        total = cur.fetchone()[0]

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT command, COUNT(*) AS count
            FROM command_log
            GROUP BY command
            ORDER BY count DESC
            LIMIT %s
            """,
            (top_n,),
        )
        top_commands = [dict(r) for r in cur.fetchall()]

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT COALESCE(category, '(none)') AS category, COUNT(*) AS count
            FROM command_log
            GROUP BY category
            ORDER BY count DESC
            LIMIT %s
            """,
            (top_n,),
        )
        top_categories = [dict(r) for r in cur.fetchall()]

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT DATE(used_at) AS day, COUNT(*) AS count
            FROM command_log
            WHERE used_at >= NOW() - INTERVAL '6 days'
            GROUP BY day
            ORDER BY day
            """
        )
        daily = [
            {"day": r["day"].isoformat() if hasattr(r["day"], "isoformat") else r["day"], "count": r["count"]}
            for r in cur.fetchall()
        ]

    conn.close()
    return {
        "total": total,
        "top_commands": top_commands,
        "top_categories": top_categories,
        "last_7_days": daily,
    }


def search_commands(
    query: str,
    limit: int = 20,
) -> list[dict]:
    """Full-text search across command, category, and context fields."""
    conn = get_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT * FROM command_log
            WHERE command  ILIKE %s
               OR category ILIKE %s
               OR context  ILIKE %s
            ORDER BY used_at DESC
            LIMIT %s
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", limit),
        )
        rows = cur.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def delete_command(row_id: int) -> bool:
    """Delete a single record by id. Returns True if a row was deleted."""
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM command_log WHERE id = %s", (row_id,))
        deleted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    d = dict(row)
    # extra is JSONB — PostgreSQL returns it as dict already; handle string fallback
    if isinstance(d.get("extra"), str):
        try:
            d["extra"] = json.loads(d["extra"])
        except Exception:
            pass
    # Serialize datetime/date objects for JSON output
    for key in ("used_at", "day"):
        if isinstance(d.get(key), (datetime, date)):
            d[key] = d[key].isoformat()
    return d

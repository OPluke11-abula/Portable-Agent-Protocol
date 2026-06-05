"""query_db — stub tool for database queries.

Replace the body of ``run`` with a real database client (e.g. SQLAlchemy,
psycopg2, sqlite3) when ready.
"""

from __future__ import annotations

from typing import Any


def run(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only database query.

    Parameters
    ----------
    params:
        connection_target : str — Named database connection (required)
        query_intent      : str — Natural-language query statement (required)
        sql               : str — legacy fallback for query_intent
        db                : str — legacy fallback for connection_target

    Returns
    -------
    dict with key ``rows``: list of row dicts.
    """
    sql: str = params.get("query_intent", params.get("sql", ""))
    db: str = params.get("connection_target", params.get("db", "default"))

    if not sql:
        return {"error": "Missing required parameter: query_intent", "rows": []}

    # --- stub: echo the query back as a single row ---
    rows = [{"db": db, "sql": sql, "note": "stub — no real database connected"}]
    return {"rows": rows}

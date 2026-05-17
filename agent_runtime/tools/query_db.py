"""query_db — stub tool for database queries.

Replace the body of ``run`` with a real database client (e.g. SQLAlchemy,
psycopg2, sqlite3) when ready.
"""

from __future__ import annotations

from typing import Any


def run(params: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only SQL query.

    Parameters
    ----------
    params:
        sql : str   — SQL SELECT statement (required)
        db  : str   — named connection key (default ``"default"``)

    Returns
    -------
    dict with key ``rows``: list of row dicts.
    """
    sql: str = params.get("sql", "")
    db: str = params.get("db", "default")

    if not sql:
        return {"error": "Missing required parameter: sql", "rows": []}

    # --- stub: echo the query back as a single row ---
    rows = [{"db": db, "sql": sql, "note": "stub — no real database connected"}]
    return {"rows": rows}

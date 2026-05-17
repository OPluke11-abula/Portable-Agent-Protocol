"""search_web — stub tool for web search.

Replace the body of ``run`` with a real search client (e.g. SerpAPI,
Bing Search, DuckDuckGo) when ready.
"""

from __future__ import annotations

from typing import Any


def run(params: dict[str, Any]) -> dict[str, Any]:
    """Search the web for *params["query"]*.

    Parameters
    ----------
    params:
        query : str   — search query (required)
        limit : int   — max results to return (default 5)

    Returns
    -------
    dict with key ``results``: list of ``{"title", "url", "snippet"}`` dicts.
    """
    query: str = params.get("query", "")
    limit: int = int(params.get("limit", 5))

    if not query:
        return {"error": "Missing required parameter: query", "results": []}

    # --- stub: return placeholder results ---
    results = [
        {
            "title": f"Result {i + 1} for '{query}'",
            "url": f"https://example.com/search?q={query.replace(' ', '+')}&page={i + 1}",
            "snippet": f"Placeholder snippet {i + 1} for query: {query}",
        }
        for i in range(limit)
    ]
    return {"results": results}

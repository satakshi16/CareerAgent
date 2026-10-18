"""internet_search and web_extract, thin wrappers over Tavily (instructions.md §11)."""
from functools import lru_cache
from typing import Literal, Optional


@lru_cache(maxsize=1)
def _search_client():
    from langchain_tavily import TavilySearch
    return TavilySearch()


@lru_cache(maxsize=1)
def _extract_client():
    from langchain_tavily import TavilyExtract
    return TavilyExtract()


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news"] = "general",
    time_range: Optional[Literal["day", "week", "month", "year"]] = None,
    include_domains: Optional[list[str]] = None,
) -> str:
    """Search the web with Tavily. Returns title, URL, date (when known), and a snippet
    for each result. Use topic="news" with a time_range for recent company news, and
    include_domains (e.g. ["youtube.com"]) to limit results to specific sites."""
    args = {"query": query, "max_results": max_results, "topic": topic}
    if time_range:
        args["time_range"] = time_range
    if include_domains:
        args["include_domains"] = include_domains
    try:
        raw = _search_client().invoke(args)
    except Exception as exc:  # network / quota / key problems go back to the agent as text
        return f"SEARCH FAILED: {exc}"
    results = raw.get("results", []) if isinstance(raw, dict) else []
    if not results:
        return f"No results for {query!r}."
    lines = []
    for i, r in enumerate(results, 1):
        date = r.get("published_date") or "date unknown"
        snippet = " ".join((r.get("content") or "").split())[:600]
        lines.append(f"{i}. {r.get('title', '(no title)')}\n   {r.get('url')}\n   {date}\n   {snippet}")
    return "\n".join(lines)


def web_extract(url: str) -> str:
    """Fetch one web page with Tavily Extract and return its clean text. Use it for
    job description URLs and for articles you need to read in full."""
    try:
        raw = _extract_client().invoke({"urls": [url]})
    except Exception as exc:
        return f"EXTRACT FAILED: {exc}"
    results = raw.get("results", []) if isinstance(raw, dict) else []
    if not results:
        failed = raw.get("failed_results") if isinstance(raw, dict) else None
        return f"EXTRACT FAILED for {url}: {failed or 'no content returned'}"
    text = results[0].get("raw_content") or ""
    return f"Source: {url}\n\n{text}"

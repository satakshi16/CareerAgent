"""internet_search and web_extract, thin wrappers over Tavily (instructions.md §11)."""
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from functools import lru_cache
from typing import Literal, Optional

# langchain_tavily posts with no timeout, so bound each call here. A timed-out request
# keeps its worker thread until the socket gives up, but the agent gets control back.
TAVILY_TIMEOUT_S = 30
EXTRACT_MAX_CHARS = 12_000
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tavily")


@lru_cache(maxsize=1)
def _search_client():
    from langchain_tavily import TavilySearch
    return TavilySearch()


@lru_cache(maxsize=1)
def _extract_client():
    from langchain_tavily import TavilyExtract
    return TavilyExtract()


def _invoke(client, args: dict):
    """client.invoke(args), raising TimeoutError after TAVILY_TIMEOUT_S seconds."""
    try:
        return _pool.submit(client.invoke, args).result(timeout=TAVILY_TIMEOUT_S)
    except FutureTimeout:
        raise TimeoutError from None


def _clean(text: str) -> str:
    """Collapse runs of spaces and blank lines, keeping paragraph breaks."""
    text = re.sub(r"[ \t\f\v]+", " ", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


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
        raw = _invoke(_search_client(), args)
    except TimeoutError:
        return "SEARCH FAILED: timeout"
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


def web_extract(url: str, max_chars: int = EXTRACT_MAX_CHARS) -> str:
    """Fetch one web page with Tavily Extract and return its clean text. Use it for
    job description URLs and for articles you need to read in full. Text past max_chars
    is cut and marked "[truncated: N of M chars]". If a job description is cut before
    its requirements, fetch again with a larger max_chars (e.g. 40000). Once an
    application exists, read its jd.md instead of fetching the URL again."""
    try:
        raw = _invoke(_extract_client(), {"urls": [url]})
    except TimeoutError:
        return "EXTRACT FAILED: timeout"
    except Exception as exc:
        return f"EXTRACT FAILED: {exc}"
    results = raw.get("results", []) if isinstance(raw, dict) else []
    if not results:
        failed = raw.get("failed_results") if isinstance(raw, dict) else None
        return f"EXTRACT FAILED for {url}: {failed or 'no content returned'}"
    text = _clean(results[0].get("raw_content") or "")
    if len(text) > max_chars:
        text = f"{text[:max_chars].rstrip()}\n\n[truncated: {max_chars} of {len(text)} chars]"
    return f"Source: {url}\n\n{text}"

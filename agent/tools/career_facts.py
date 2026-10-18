"""append_career_fact: the only writer of data/career_facts.md (§6.4).

Existing lines are never changed. A new entry goes at the end of its section
(the section is created at the end of the file if it doesn't exist yet).
"""
import os
import re
import tempfile
import threading
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Literal

from agent import config

DUPLICATE_RATIO = 0.85
# The agent often calls this tool several times in parallel (tool calls run in a
# thread pool), so every read-modify-write of the file holds this lock.
_LOCK = threading.Lock()
_ENTRY_RE = re.compile(r"^- \[[^\]]*\]\s*(?:REJECTED:\s*)?(.*)$")


def _normalize(text: str) -> str:
    text = re.sub(r"\((?:user-confirmed|rejected)[^)]*\)", "", text, flags=re.IGNORECASE)
    text = text.replace("Do not ask again.", "")
    return " ".join(re.sub(r"[^a-z0-9%$.,]+", " ", text.lower()).split())


def find_duplicate(lines: list[str], fact: str) -> str | None:
    target = _normalize(fact)
    for line in lines:
        m = _ENTRY_RE.match(line.strip())
        if not m:
            continue
        existing = _normalize(m.group(1))
        if existing == target or SequenceMatcher(None, existing, target).ratio() >= DUPLICATE_RATIO:
            return line.strip()
    return None


def add_fact(path: Path, section: str, fact: str, status: str, source_app: str,
             today: date | None = None) -> str:
    with _LOCK:
        return _add_fact(path, section, fact, status, source_app, today)


def _add_fact(path, section, fact, status, source_app, today):
    section = section.strip().lstrip("#").strip()
    fact = re.sub(r"^\s*REJECTED:\s*", "", " ".join(fact.split()), flags=re.IGNORECASE)
    if status not in ("confirmed", "rejected"):
        return f"ERROR: status must be 'confirmed' or 'rejected', not {status!r}."
    if not section or not fact:
        return "ERROR: section and fact are both required."
    source_app = Path(source_app.rstrip("/")).name or "manual"

    text = path.read_text(encoding="utf-8") if path.exists() else "# Career Facts\n"
    lines = text.splitlines()
    dup = find_duplicate(lines, fact)
    if dup:
        return f"REFUSED: near-duplicate of an existing entry, nothing written.\nExisting: {dup}"

    stamp = f"[{(today or date.today()).isoformat()} | {source_app}]"
    if status == "rejected":
        entry = f"- {stamp} REJECTED: {fact.rstrip('.')}. Do not ask again."
    else:
        entry = f"- {stamp} {fact}" + ("" if "user-confirmed" in fact else " (user-confirmed)")

    heading = f"## {section}"
    idx = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if idx is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", heading, "", entry]
    else:
        end = next((i for i in range(idx + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        insert_at = end
        while insert_at > idx + 1 and not lines[insert_at - 1].strip():
            insert_at -= 1
        if insert_at == idx + 1:  # empty section: keep a blank line under the heading
            lines[insert_at:insert_at] = ["", entry]
        else:
            lines.insert(insert_at, entry)

    _write_atomic(path, "\n".join(lines) + "\n")
    return f"Saved under '{heading}': {entry}"


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def append_career_fact(section: str, fact: str, status: Literal["confirmed", "rejected"],
                       source_app: str) -> str:
    """Save one user-confirmed fact or metric (status="confirmed"), or record a metric
    the user declined (status="rejected") so it is never asked again, in
    data/career_facts.md. section is the employer/role heading, e.g.
    "Acme Analytics · Data Science Manager (Oct 2022 – Present)", or "General / Skills".
    source_app is the application folder name. Refuses near-duplicates."""
    try:
        return add_fact(config.CAREER_FACTS, section, fact, status, source_app)
    except OSError as exc:
        return f"ERROR: could not write career facts: {exc}. Nothing was saved; retry this fact."

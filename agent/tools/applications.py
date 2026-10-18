"""create_application, load_application, update_application_state (§2.2, §11).

state.json in each application folder is the handoff contract between the
orchestrator and the subagents.
"""
import json
import os
import re
import tempfile
import threading
from datetime import date
from pathlib import Path
from typing import Any, Optional

from agent import config

_LOCK = threading.Lock()  # parallel tool calls may update the same state.json


def slugify(text: str) -> str:
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "unknown"


def _app_dir(app_dir: str) -> Path:
    path = config.resolve(app_dir)
    if path.parent != config.APPLICATIONS_DIR.resolve():
        raise ValueError(f"{app_dir!r} is not an application folder under /applications/.")
    return path


def _read_state(path: Path) -> dict:
    state_file = path / "state.json"
    return json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}


def _write_state(path: Path, state: dict) -> None:
    fd, tmp = tempfile.mkstemp(dir=path, prefix=".state.json.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(state, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path / "state.json")
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _summary(path: Path) -> str:
    files = sorted(p.name for p in path.iterdir() if p.is_file() and not p.name.startswith("."))
    return (f"app_dir: {config.virtual(path)}\n"
            f"state.json:\n{json.dumps(_read_state(path), indent=2, ensure_ascii=False)}\n"
            f"files: {', '.join(files) or '(none)'}")


def create_application(company: str, role: str, jd_text: str, cover_letter: bool,
                       jd_url: Optional[str] = None, notes: Optional[str] = None,
                       reuse_existing: bool = False, route: str = "resume") -> str:
    """Create the application folder applications/<company>_<role>_<YYYY-MM-DD>/ with
    jd.md and state.json, and return its app_dir. If a folder for the same company and
    role already exists, nothing is created: the existing folders are listed so you can
    ask the user. Call again with reuse_existing=True to continue the most recent one.
    route is "resume" or "interview" (an application opened only for interview prep)."""
    if not jd_text.strip():
        return "ERROR: jd_text is empty. Get the job description text first (web_extract for a URL)."
    prefix = f"{slugify(company)}_{slugify(role)}"
    root = config.APPLICATIONS_DIR
    root.mkdir(parents=True, exist_ok=True)
    existing = sorted(p for p in root.glob(f"{prefix}_*") if p.is_dir())
    if existing and reuse_existing:
        return "REUSED existing application.\n" + _summary(existing[-1])
    if existing:
        listing = "\n".join(f"- {config.virtual(p)}" for p in existing)
        return ("EXISTS: an application for this company and role already exists:\n"
                f"{listing}\nAsk the user whether to continue it (reuse_existing=True) "
                "or start fresh with a different role label.")

    path = root / f"{prefix}_{date.today().isoformat()}"
    path.mkdir()
    header = [f"# {role} at {company}", "", f"- Saved: {date.today().isoformat()}"]
    if jd_url:
        header.append(f"- Source: {jd_url}")
    if notes:
        header.append(f"- User notes: {notes}")
    (path / "jd.md").write_text("\n".join(header) + "\n\n---\n\n" + jd_text.strip() + "\n",
                                encoding="utf-8")
    _write_state(path, {
        "route": route,
        "company": company,
        "role": role,
        "app_dir": config.virtual(path),
        "cover_letter": bool(cover_letter),
        "notes": notes or "",
        "stage": "S0_intake",
        "completed": [],
        "draft": None,
        "open_questions": [],
    })
    return "CREATED.\n" + _summary(path)


def load_application(app_dir: Optional[str] = None, company: Optional[str] = None,
                     role: Optional[str] = None) -> str:
    """Return state.json and the file list for an application. Pass app_dir, or
    company (and optionally role) to find the most recent matching folder."""
    try:
        if app_dir:
            path = _app_dir(app_dir)
        elif company:
            pattern = f"{slugify(company)}_{slugify(role)}_*" if role else f"{slugify(company)}_*"
            matches = sorted(p for p in config.APPLICATIONS_DIR.glob(pattern) if p.is_dir())
            if not matches:
                return f"NOT FOUND: no application matches {pattern!r}."
            path = matches[-1]
        else:
            return "ERROR: pass app_dir, or company (and optionally role)."
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not path.is_dir():
        return f"NOT FOUND: {app_dir}"
    return _summary(path)


def update_application_state(app_dir: str, updates: dict[str, Any]) -> str:
    """Merge updates into <app_dir>/state.json (e.g. {"stage": "S2_elicitation",
    "completed": [...], "draft": "tailored_resume_v1.yaml", "open_questions": [...]}).
    Keys you leave out keep their current values. Use this, not write_file, for state.json."""
    try:
        path = _app_dir(app_dir)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not (path / "state.json").exists():
        return f"ERROR: {app_dir} has no state.json. Was it made with create_application?"
    with _LOCK:
        state = _read_state(path)
        state.update({k: v for k, v in updates.items() if k != "app_dir"})
        _write_state(path, state)
    return "Updated state.json:\n" + json.dumps(state, indent=2, ensure_ascii=False)

"""validate_resume and render_resume_pdf, using PDFResumeGenerator as a library (§11).

Both return text instead of raising, so the agent can fix the YAML and retry.
render_resume_pdf pauses for the user's approval first. The user replies in plain
text ("approve", "edit <section>: <new text>", "reject: <reason>") instead of the
JSON that langchain's HumanInTheLoopMiddleware expects.
"""
import re

import yaml
from langgraph.types import interrupt

from agent.config import APPLICATIONS_DIR, resolve, virtual
from agent.tools.style_lint import style_lint
from resume_generator import generate
from resume_generator.errors import ResumeError


def _fit_notes(info: dict) -> str:
    notes = []
    if info["extra_scale"] < 1:
        notes.append(f"section/entry spacing at {info['extra_scale']:.0%}")
    if info["leading_scale"] < 1:
        notes.append(f"line spacing at {info['leading_scale']:.0%}")
    if info["auto_shrink"]:
        notes.append(f"text auto-shrunk by {-info['auto_shrink']:g} pt")
    return ", ".join(notes) if notes else "none (natural reference spacing)"


def _warnings(info: dict) -> str:
    return "".join(f"\nwarning: {w}" for w in info["warnings"])


def _error(exc: ResumeError) -> str:
    return f"ERROR (exit_code {exc.exit_code}, {type(exc).__name__}):\n{exc}"


def validate_resume(yaml_path: str) -> str:
    """Validate a resume YAML and confirm it fits on one page, without writing a PDF.
    Returns 'OK' with fit adjustments, or the generator's errors with YAML line numbers."""
    try:
        info = generate(str(resolve(yaml_path)), check_only=True, strict=False)
    except (ResumeError, ValueError) as exc:
        return _error(exc) if isinstance(exc, ResumeError) else f"ERROR: {exc}"
    return (f"OK: {info['pages']} page, {info['font']} {info['body_size']:g} pt body. "
            f"Fit adjustments: {_fit_notes(info)}.{_warnings(info)}")


def check_draft(yaml_path: str) -> str:
    """Run style_lint and validate_resume on a resume YAML draft in one call. Both
    must pass (STYLE: CLEAN and FIT: OK) before you show the draft to the user."""
    return f"STYLE: {style_lint(yaml_path)}\nFIT: {validate_resume(yaml_path)}"


APPROVE_WORDS = {"approve", "approved", "yes", "y", "ok", "okay", "lgtm", "ship it", "looks good"}
REJECT_WORDS = {"reject", "rejected", "no", "n", "cancel", "stop"}
ASK = ('Reply "approve", "edit <section>: <new text>" (for example '
       '"edit experience / Acme Analytics: <new bullet>"), or "reject: <reason>".')


def parse_decision(reply, sections: list[str]) -> tuple[str, str, str] | str:
    """Turn the user's reply into (kind, section, text), or return a hint for a re-ask.
    kind is "approve", "edit", or "reject". Also accepts the old {"decisions": [...]} JSON."""
    if isinstance(reply, dict) and reply.get("decisions"):
        first = reply["decisions"][0] if isinstance(reply["decisions"], list) else {}
        reply = first.get("type", "") if isinstance(first, dict) else ""
    if not isinstance(reply, str):
        return f"I couldn't read that reply ({reply!r})."
    text = reply.strip().strip('"\'').strip()
    word = text.lower().rstrip(".!")
    if word in APPROVE_WORDS:
        return ("approve", "", "")
    head, _, rest = text.partition(":")
    if head.strip().lower() in REJECT_WORDS or word in REJECT_WORDS:
        return ("reject", "", rest.strip())
    m = re.match(r"edit\b\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    if not m:
        return f"I didn't understand {text!r}."
    section, sep, new_text = m.group(1).partition(":")
    section, new_text = section.strip(), new_text.strip()
    if not sep or not section or not new_text:
        return "An edit needs a section and the new text, separated by a colon."
    base = section.split("/")[0].strip().lower()
    if base not in sections:
        return f"There is no section {base!r}. Sections: {', '.join(sections)}."
    return ("edit", section, new_text)


def _render(yaml_file, out) -> str:
    try:
        info = generate(str(yaml_file), str(out), font="auto", allow_multipage=False)
    except ResumeError as exc:
        return _error(exc)
    except ValueError as exc:
        return f"ERROR: {exc}"
    return (f"Wrote {virtual(info['output'])}: {info['pages']} page, font {info['font']}, "
            f"{info['body_size']:g} pt body. Fit adjustments: {_fit_notes(info)}.{_warnings(info)}")


def render_resume_pdf(yaml_path: str, output_path: str, changes: str = "") -> str:
    """Render the approved resume YAML to a one-page PDF inside the application folder.
    output_path should be <app_dir>/<Name>_Resume_<Company>.pdf. Never renders multiple pages.
    Pauses for the user's approval first. changes: one line on what changed since the user
    last saw this draft (leave empty the first time)."""
    try:
        out = resolve(output_path)
        if not out.is_relative_to(APPLICATIONS_DIR.resolve()):
            return "ERROR: output_path must be inside /applications/<app_dir>/."
        if out.suffix.lower() != ".pdf":
            out = out.with_name(out.name + ".pdf")
        yaml_file = resolve(yaml_path)
        resume = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
    except (ValueError, OSError, yaml.YAMLError) as exc:
        return f"ERROR: {exc}"
    sections = [k for k in resume if k != "name"] if isinstance(resume, dict) else []

    # interrupt() must stay outside any try/except: it pauses by raising.
    question = f"Render {virtual(out)}? {ASK}"
    while True:
        reply = interrupt({"question": question, "changes": changes or "(first render)",
                           "file": virtual(yaml_file), "resume": resume})
        decision = parse_decision(reply, sections)
        if isinstance(decision, tuple):
            break
        question = f"{decision} {ASK}"

    kind, section, text = decision
    if kind == "reject":
        return f"REJECTED by the user. PDF not rendered. Reason: {text or '(none given)'}"
    if kind == "edit":
        return ("EDIT REQUESTED by the user. PDF not rendered.\n"
                f"Section: {section}\nNew text (user's exact words):\n{text}\n"
                "Apply this edit, then call render_resume_pdf again with `changes` set.")
    return _render(yaml_file, out)

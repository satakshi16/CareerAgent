"""style_lint: deterministic check against the §9 hard bans.

For a resume YAML, only content fields are checked (headline, summary, bullets,
skill items). Names, titles, dates, contact, and education are copied from the
master and the generator adds its own separators, so those are skipped.
"""
import re
from pathlib import Path

import yaml

from agent.config import resolve

BUZZWORDS = [
    r"spearhead(?:s|ed|ing)?", r"leverag(?:e|es|ed|ing)", r"utiliz(?:e|es|ed|ing|ation)",
    r"synerg(?:y|ies|istic)", r"robust", r"seamless(?:ly)?", r"cutting[- ]edge",
    r"state[- ]of[- ]the[- ]art", r"passionate", r"dynamic", r"results[- ]driven",
    r"proven track record", r"delv(?:e|es|ed|ing)", r"tapestry", r"landscape", r"realm",
    r"holistic(?:ally)?", r"game[- ]changer", r"transformative", r"innovative solutions?",
    r"fast[- ]paced environment", r"thrilled",
    r"in today['’]s world", r"hope this (?:message |email |note )?finds you well",
]
_BUZZ_RE = re.compile(r"\b(?:" + "|".join(BUZZWORDS) + r")\b", re.IGNORECASE)
_EXCITED_OPENER_RE = re.compile(
    r"(?:^|[.!?]\s+|\n\s*)((?:I['’]?m |I am |We['’]re )?(?:so |really |very )?excited to)\b",
    re.IGNORECASE)
_EM_DASH_RE = re.compile(r"[—―]|(?<=\S)--|--(?=\s)")
_AS_A_RE = re.compile(r"(?:^|[.!?]\s+|\n\s*)(As an? \w+)", re.IGNORECASE)
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿️‍]")
# Plain characters only in resume fields: no arrows, bullets, stars, smart quotes, etc.
_RESUME_SYMBOL_RE = re.compile(
    "[←-⇿•■-◿★☆✓✔→‘’“”…·]")


def lint_text(text: str, field: str = "text", resume_field: bool = False) -> list[dict]:
    """Return a list of violations: {field, rule, match}."""
    found = []

    def add(rule, match):
        found.append({"field": field, "rule": rule, "match": match})

    for m in _EM_DASH_RE.finditer(text):
        add("em-dash", _context(text, m))
    for m in _BUZZ_RE.finditer(text):
        add("buzzword", m.group(0))
    for m in _EXCITED_OPENER_RE.finditer(text):
        add("buzzword", m.group(1))
    for m in _EMOJI_RE.finditer(text):
        add("emoji", f"U+{ord(m.group(0)):04X}")
    if resume_field:
        for m in _RESUME_SYMBOL_RE.finditer(text):
            add("decorative-symbol", f"{m.group(0)!r} (U+{ord(m.group(0)):04X})")
    return found


def lint_as_a(texts: list[tuple[str, str]]) -> list[dict]:
    """'As a ...' may open at most one sentence per document."""
    hits = [(field, m.group(1)) for field, text in texts for m in _AS_A_RE.finditer(text)]
    return [{"field": f, "rule": "as-a-repeat", "match": s} for f, s in hits[1:]]


def resume_content_fields(data: dict) -> list[tuple[str, str]]:
    fields = []
    if isinstance(data.get("headline"), str):
        fields.append(("headline", data["headline"]))
    if isinstance(data.get("summary"), str):
        fields.append(("summary", data["summary"]))
    for i, job in enumerate(data.get("experience") or []):
        for j, bullet in enumerate(job.get("bullets") or []):
            fields.append((f"experience[{i}].bullets[{j}]", str(bullet)))
    for i, skill in enumerate(data.get("skills") or []):
        items = skill.get("items")
        items = ", ".join(map(str, items)) if isinstance(items, list) else str(items or "")
        fields.append((f"skills[{i}].items", items))
    return fields


def lint(text_or_yaml_path: str) -> list[dict]:
    """Lint plain text, a resume YAML (.yaml/.yml path), or a markdown/text file (.md/.txt path)."""
    candidate = text_or_yaml_path.strip()
    if candidate.endswith((".yaml", ".yml")) and "\n" not in candidate:
        path = resolve(candidate)
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        fields = resume_content_fields(data)
        found = [v for name, text in fields for v in lint_text(text, name, resume_field=True)]
        return found + lint_as_a(fields)
    if candidate.endswith((".md", ".txt")) and "\n" not in candidate:
        # Prep docs and messages are linted by path so the agent doesn't resend the text.
        text = Path(resolve(candidate)).read_text(encoding="utf-8")
        return lint_text(text, candidate) + lint_as_a([(candidate, text)])
    return lint_text(text_or_yaml_path) + lint_as_a([("text", text_or_yaml_path)])


def style_lint(text_or_yaml_path: str) -> str:
    """Check writing against the hard style bans (em dashes, buzzwords, repeated
    'As a ...' openers, emoji, decorative symbols in resume fields). Pass the text
    itself, a path to a resume YAML, or a path to a .md file (cheaper than pasting a
    long document). Returns 'CLEAN' or the list of violations."""
    try:
        found = lint(text_or_yaml_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return f"ERROR: could not lint: {exc}"
    if not found:
        return "CLEAN: no style violations."
    lines = [f"{len(found)} violation(s):"]
    lines += [f"- {v['field']}: {v['rule']}: {v['match']}" for v in found]
    return "\n".join(lines)


def _context(text: str, m: re.Match, width: int = 25) -> str:
    start, end = max(0, m.start() - width), min(len(text), m.end() + width)
    return "..." + text[start:end].replace("\n", " ") + "..."

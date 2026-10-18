"""
Load resume content from YAML and validate it into immutable dataclasses.

All problems are collected and reported together, each tagged with the YAML
line number and a field path such as  experience[1].bullets[0].
"""
import datetime as _dt
import difflib
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .template import HEADLINE_SEPARATOR as T_SEP

import yaml

from .errors import ConfigError, ValidationError


# ---------------------------------------------------------------- data model
@dataclass(frozen=True)
class ContactItem:
    text: str
    url: Optional[str] = None


@dataclass(frozen=True)
class Job:
    company: str
    location: Optional[str]
    title: str
    start: str
    end: str
    bullets: Tuple[str, ...]


@dataclass(frozen=True)
class School:
    school: str
    location: Optional[str]
    date: str
    degree: str


@dataclass(frozen=True)
class SkillLine:
    label: str
    items: str


@dataclass(frozen=True)
class Resume:
    name: str
    contact: Tuple[ContactItem, ...]
    summary: str
    experience: Tuple[Job, ...]
    education: Tuple[School, ...]
    skills: Tuple[SkillLine, ...]
    headline: Optional[str] = None

    def iter_texts(self):
        """Yield (field_path, text) for every string that will be printed."""
        yield "name", self.name
        for i, c in enumerate(self.contact):
            yield f"contact[{i}].text", c.text
        if self.headline:                                               
            yield "headline", self.headline
        yield "summary", self.summary
        for i, j in enumerate(self.experience):
            for key in ("company", "location", "title", "start", "end"):
                if getattr(j, key):
                    yield f"experience[{i}].{key}", getattr(j, key)
            for k, b in enumerate(j.bullets):
                yield f"experience[{i}].bullets[{k}]", b
        for i, s in enumerate(self.education):
            for key in ("school", "location", "date", "degree"):
                if getattr(s, key):
                    yield f"education[{i}].{key}", getattr(s, key)
        for i, s in enumerate(self.skills):
            yield f"skills[{i}].label", s.label
            yield f"skills[{i}].items", s.items


# ------------------------------------------------------------ schema (keys)
TOP_KEYS = {"name": True, "contact": True, "headline": False, "summary": True,
            "experience": True, "education": True, "skills": True}
CONTACT_KEYS = {"text": True, "url": False}
JOB_KEYS = {"company": True, "location": False, "title": True,
            "start": True, "end": True, "bullets": True}
SCHOOL_KEYS = {"school": True, "location": False, "date": True, "degree": True}
SKILL_KEYS = {"label": True, "items": True}

URL_RE = re.compile(r"^(https?://[^\s/$.?#][^\s]*|mailto:[^\s@]+@[^\s@]+\.[^\s@]+)$", re.I)
_INVISIBLE = {"\u00ad": "soft hyphen", "\u200b": "zero-width space",
              "\ufeff": "byte-order mark", "\u200e": "LTR mark", "\u200f": "RTL mark"}


# ------------------------------------------------- YAML line-number index
def _index_lines(node, path="", index=None, dupes=None):
    """Map field paths to 1-based YAML line numbers; record duplicate keys."""
    if index is None:
        index, dupes = {}, []
    index[path] = node.start_mark.line + 1
    if isinstance(node, yaml.MappingNode):
        seen = set()
        for key_node, val_node in node.value:
            key = str(key_node.value)
            child = f"{path}.{key}" if path else key
            if key in seen:
                dupes.append((child, key_node.start_mark.line + 1))
            seen.add(key)
            _index_lines(val_node, child, index, dupes)
    elif isinstance(node, yaml.SequenceNode):
        for i, item in enumerate(node.value):
            _index_lines(item, f"{path}[{i}]", index, dupes)
    return index, dupes


class _Validator:
    def __init__(self, lines, source):
        self.lines, self.source = lines, source
        self.errors, self.warnings = [], []

    def _where(self, path):
        p = path
        while p:
            if p in self.lines:
                return f"{self.source}:{self.lines[p]}: {path}"
            parent = re.sub(r"(\.[^.\[]+|\[\d+\])$", "", p)
            p = "" if parent == p else parent      # top-level key: stop
        if "" in self.lines and path:
            return f"{self.source}:{self.lines['']}: {path}"
        return f"{self.source}: {path or '(top level)'}"

    def error(self, path, msg):
        self.errors.append(f"{self._where(path)}: {msg}")

    def warn(self, path, msg):
        self.warnings.append(f"{self._where(path)}: {msg}")

    # ---- structural helpers
    def mapping(self, obj, path, schema):
        if not isinstance(obj, dict):
            self.error(path, f"expected a mapping of fields, got {_kind(obj)}")
            return None
        for key in obj:
            if key not in schema:
                hint = difflib.get_close_matches(str(key), schema, n=1)
                extra = f" (did you mean '{hint[0]}'?)" if hint else \
                        f" (allowed: {', '.join(schema)})"
                self.error(_join(path, key), f"unknown field '{key}'{extra}")
        for key, required in schema.items():
            if required and (key not in obj or obj[key] is None):
                self.error(_join(path, key), "required field is missing or empty")
        return obj

    def sequence(self, obj, path, min_items=1):
        if obj is None:
            return []
        if not isinstance(obj, list):
            self.error(path, f"expected a list (lines starting with '- '), got {_kind(obj)}")
            return []
        if len(obj) < min_items:
            self.error(path, f"needs at least {min_items} item(s)")
        return obj

    def text(self, obj, path, required=True):
        if obj is None:
            return None               # 'missing' already reported by mapping()
        if isinstance(obj, bool):
            self.error(path, f"YAML read this as the boolean {obj}; put the value "
                             "in quotes (e.g. \"Yes\") if it is meant to be text")
            return None
        if isinstance(obj, (_dt.date, _dt.datetime)):
            self.warn(path, f"YAML read this as a date; printing it as '{obj.isoformat()}'. "
                            "Quote the value to control its exact text")
            obj = obj.isoformat()
        elif isinstance(obj, float):
            self.warn(path, f"YAML read this as a number ({obj!r}); quote it to keep "
                            "exact formatting such as trailing zeros")
            obj = repr(obj)
        elif isinstance(obj, int):
            obj = str(obj)
        elif not isinstance(obj, str):
            self.error(path, f"expected text, got {_kind(obj)}")
            return None
        return self._clean(obj, path, required)

    def _clean(self, s, path, required):
        s = unicodedata.normalize("NFC", s)
        for ch, label in _INVISIBLE.items():
            if ch in s:
                self.warn(path, f"removed invisible character ({label}, U+{ord(ch):04X})")
                s = s.replace(ch, "")
        s = re.sub(r"[\t\r\n\v\f]+", " ", s)
        bad = sorted({c for c in s if unicodedata.category(c) == "Cc"})
        if bad:
            codes = ", ".join(f"U+{ord(c):04X}" for c in bad)
            self.error(path, f"contains control characters ({codes})")
            return None
        s = re.sub(r" {2,}", " ", s).strip()
        if not s and required:
            self.error(path, "must not be blank")
            return None
        return s or None


def _join(path, key):
    return f"{path}.{key}" if path else str(key)


def _kind(obj):
    return {dict: "a mapping", list: "a list", str: "text", type(None): "nothing"}.get(
        type(obj), type(obj).__name__)


# -------------------------------------------------------------- public API
def load_resume(path) -> Tuple[Resume, list]:
    """Parse and validate the YAML file. Returns (resume, warnings)."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ConfigError(f"Resume file not found: {path}")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"{path} is not valid UTF-8 text ({exc}). Re-save it as UTF-8.")
    except OSError as exc:
        raise ConfigError(f"Cannot read {path}: {exc}")
    return parse_resume(raw, source=path.name)


def parse_resume(raw: str, source="resume.yaml") -> Tuple[Resume, list]:
    try:
        node = yaml.compose(raw, Loader=yaml.SafeLoader)
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f"{source}:{mark.line + 1}:{mark.column + 1}" if mark else source
        problem = getattr(exc, "problem", None) or str(exc)
        hint = ("Values that start with '**' (bold markup) must be in quotes."
                if "'*'" in problem else
                "Check indentation and quote values containing ': ' or '#'.")
        raise ConfigError(f"{where}: YAML syntax error: {problem}. {hint}")
    if node is None:
        raise ConfigError(f"{source} is empty.")

    lines, dupes = _index_lines(node)
    v = _Validator(lines, source)
    for dup_path, line in dupes:
        v.errors.append(f"{source}:{line}: {dup_path}: field appears more than once "
                        "(YAML silently keeps only the last one)")

    top = v.mapping(data, "", TOP_KEYS) or {}

    name = v.text(top.get("name"), "name")

    contact = []
    for i, item in enumerate(v.sequence(top.get("contact"), "contact")):
        p = f"contact[{i}]"
        if isinstance(item, (str, int)) and not isinstance(item, bool):
            t = v.text(item, p)
            if t:
                contact.append(ContactItem(t))
            continue
        m = v.mapping(item, p, CONTACT_KEYS)
        if m is None:
            continue
        t = v.text(m.get("text"), f"{p}.text")
        url = v.text(m.get("url"), f"{p}.url", required=False)
        if url and not URL_RE.match(url):
            v.error(f"{p}.url", f"'{url}' is not a valid link; it must start with "
                                "https://, http:// or mailto:")
            url = None
        if t:
            contact.append(ContactItem(t, url))

    summary = v.text(top.get("summary"), "summary")

    headline = top.get("headline")
    if isinstance(headline, list):
        parts = [v.text(x, f"headline[{k}]") for k, x in enumerate(headline)]
        headline = T_SEP.join(p for p in parts if p) or None
    else:
        headline = v.text(headline, "headline", required=False)

    jobs = []
    for i, item in enumerate(v.sequence(top.get("experience"), "experience")):
        p = f"experience[{i}]"
        m = v.mapping(item, p, JOB_KEYS)
        if m is None:
            continue
        fields = {k: v.text(m.get(k), f"{p}.{k}", required=JOB_KEYS[k])
                  for k in ("company", "location", "title", "start", "end")}
        bullets = []
        for k, b in enumerate(v.sequence(m.get("bullets"), f"{p}.bullets")):
            t = v.text(b, f"{p}.bullets[{k}]")
            if t:
                bullets.append(t)
        if all(fields[k] for k in ("company", "title", "start", "end")) and bullets:
            jobs.append(Job(bullets=tuple(bullets), **fields))

    schools = []
    for i, item in enumerate(v.sequence(top.get("education"), "education")):
        p = f"education[{i}]"
        m = v.mapping(item, p, SCHOOL_KEYS)
        if m is None:
            continue
        fields = {k: v.text(m.get(k), f"{p}.{k}", required=SCHOOL_KEYS[k])
                  for k in SCHOOL_KEYS}
        if all(fields[k] for k in ("school", "date", "degree")):
            schools.append(School(**fields))

    skills = []
    for i, item in enumerate(v.sequence(top.get("skills"), "skills")):
        p = f"skills[{i}]"
        m = v.mapping(item, p, SKILL_KEYS)
        if m is None:
            continue
        label = v.text(m.get("label"), f"{p}.label")
        if label:
            label = label.rstrip(":").rstrip()   # the template adds the colon
        items = m.get("items")
        if isinstance(items, list):
            parts = [v.text(x, f"{p}.items[{k}]") for k, x in enumerate(items)]
            items = ", ".join(x for x in parts if x) if all(parts) and parts else None
            if not parts:
                v.error(f"{p}.items", "list is empty")
        else:
            items = v.text(items, f"{p}.items")
        if label and items:
            skills.append(SkillLine(label, items))

    if v.errors:
        raise ValidationError(v.errors)

    resume = Resume(name=name, contact=tuple(contact), summary=summary,
                    experience=tuple(jobs), education=tuple(schools), skills=tuple(skills),
                    headline=headline)
    return resume, v.warnings

MARKUP_FIELDS = re.compile(r"^(summary|experience\[\d+\]\.bullets\[\d+\]|"
                           r"education\[\d+\]\.degree|skills\[\d+\]\.items)$")


def check_markup(resume: Resume) -> None:
    """'**' must come in pairs, and only in fields that support bold markup."""
    problems = []
    for path, text in resume.iter_texts():
        count = text.count("**")
        if not count:
            continue
        if not MARKUP_FIELDS.match(path):
            problems.append(f"{path}: '**' bold markup is not supported in this field")
        elif count % 2:
            problems.append(f"{path}: unmatched '**' (bold markup must open and close)")
        elif "****" in text:
            problems.append(f"{path}: empty bold markup '****'")
    if problems:
        raise ValidationError(problems)
    

def check_glyphs(resume: Resume, fonts) -> None:
    """Fail if any printed character is absent from the chosen font family."""
    problems = []
    for path, text in resume.iter_texts():
        missing = fonts.missing_glyphs(text)
        if missing:
            shown = ", ".join(f"'{c}' (U+{ord(c):04X} {unicodedata.name(c, 'unnamed')})"
                              for c in missing)
            problems.append(f"{path}: character(s) not available in font "
                            f"{fonts.family}: {shown}. Replace or remove them.")
    if problems:
        raise ValidationError(problems)

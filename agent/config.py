"""Paths, model choice, and the virtual-path mapping shared by all tools.

The agent's filesystem backend runs with virtual_mode=True, so the agent sees
"/" as the repo root. Tools receive those virtual paths and map them back here.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
APPLICATIONS_DIR = REPO_ROOT / "applications"
PROMPTS_DIR = REPO_ROOT / "agent" / "prompts"
GENERATOR_DIR = REPO_ROOT / "PDFResumeGenerator"


def _or_example(path: Path) -> Path:
    """Personal files are gitignored. A fresh clone uses the committed sample
    (master_resume.example.yaml for master_resume.yaml) until the real one exists."""
    example = path.with_name(f"{path.stem}.example{path.suffix}")
    return example if not path.exists() and example.exists() else path


MASTER_RESUME = _or_example(DATA_DIR / "master_resume.yaml")
AGENTS_MD = _or_example(REPO_ROOT / "AGENTS.md")
# No fallback: sample facts must never mix with a real resume, and
# append_career_fact must never write into the committed sample. The tool
# creates this file on the first append.
CAREER_FACTS = DATA_DIR / "career_facts.md"

MODEL = os.environ.get("CAREER_AGENT_MODEL", "openai:gpt-5.5")

# Make `from resume_generator import generate` work without installing the package.
if str(GENERATOR_DIR) not in sys.path:
    sys.path.insert(0, str(GENERATOR_DIR))


def resolve(path: str) -> Path:
    """Map an agent path ("/applications/x/y.yaml" or "applications/x/y.yaml") to a
    real path inside the repo. Raises ValueError for anything outside the repo."""
    root = REPO_ROOT.resolve()
    p = Path(path).expanduser()
    if p.is_absolute() and p.resolve().is_relative_to(root):
        real = p.resolve()
    else:
        real = (root / str(path).lstrip("/")).resolve()
    if not real.is_relative_to(root):
        raise ValueError(f"Path {path!r} is outside the project folder.")
    return real


def virtual(path: Path) -> str:
    """Real path inside the repo -> the "/..." path the agent sees."""
    return "/" + path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def load_prompt(name: str) -> str:
    """Prompts name the real files; point them at the samples when those are in use."""
    text = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    return (text.replace("/data/master_resume.yaml", virtual(MASTER_RESUME))
                .replace("/AGENTS.md", virtual(AGENTS_MD)))

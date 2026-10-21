"""load_stage_context: everything a subagent stage starts from, in one tool call.

Subagents remember nothing between calls (§2.2), so each stage used to begin with a
string of separate reads (state, master resume, facts, JD, earlier stage files,
SKILL.md files), each one a full model round trip. This returns them together.

STAGES mirrors the "Read" and "Skills" columns of the stage tables in
agent/prompts/resume_tailor.md and interview_coach.md. tests/test_stage_context.py
fails if the two drift apart.
"""
import re
from pathlib import Path
from typing import Optional

from agent import config
from agent.tools.applications import _app_dir, _read_state, _summary

SKILLS_DIR = config.REPO_ROOT / "skills"
MASTER = "/data/master_resume.yaml"
FACTS = "/data/career_facts.md"
LATEST_DRAFT = "<latest tailored_resume_vN.yaml>"

# files: names inside the application folder, MASTER/FACTS, LATEST_DRAFT, or a tuple
# meaning "the first of these that exists". cover_letter: added when state says so.
STAGES: dict[str, dict] = {
    # resume-tailor
    "S0_intake": {"files": ["jd.md", MASTER, FACTS],
                  "skills": ["company-research", "jd-gap-analysis"]},
    "S1_gap_analysis": {"files": ["jd.md", "gap_analysis.md", MASTER, FACTS],
                        "skills": ["metric-elicitation"]},
    "S2_elicitation": {"files": ["jd.md", "company_brief.md", "gap_analysis.md",
                                 "elicitation.md", MASTER, FACTS],
                       "skills": ["xyz-bullet-writing", "resume-yaml-format",
                                  "ats-hm-scan", "no-fabrication"]},
    "S4_review": {"files": [LATEST_DRAFT, "changes.md", MASTER, FACTS],
                  "skills": ["resume-yaml-format", "no-fabrication"],
                  "cover_letter": {"files": ["jd.md", "company_brief.md"],
                                   "skills": ["cover-letter"]}},
    "S5_render": {"files": [LATEST_DRAFT, "changes.md"],
                  "skills": ["resume-yaml-format"]},
    "done": {"files": [], "skills": []},
    # interview-coach
    "I0_intake": {"files": ["jd.md", "company_brief.md", ("tailored_resume_final.yaml", MASTER),
                            FACTS, "gap_analysis.md"],
                  "skills": ["prep-doc", "company-research", "<round>", "why-this-role",
                             "explain-simply*", "study-resources*", "human-writing",
                             "no-fabrication"]},
    # I1 and I2 read only parts of the prep file (grep, then read_file with offset).
    "I1_review": {"files": [], "skills": ["mock-drill"]},
    "I2_drill": {"files": [], "skills": ["mock-drill"]},
}

ROUND_SKILLS = {"recruiter_screen": "recruiter-screen", "hiring_manager": "hiring-manager",
                "technical": "technical-round", "behavioral": "behavioral-star"}
TEACHING_ROUNDS = {"technical", "hiring_manager"}   # skills marked * load only for these


def _rounds(round_value: Optional[str]) -> list[str]:
    """'technical-behavioral', 'technical, behavioral' -> ['technical', 'behavioral']."""
    return [r for r in re.split(r"[\s,/+-]+", (round_value or "").lower()) if r in ROUND_SKILLS]


def stage_skills(stage: str, state: dict, round_value: Optional[str] = None) -> list[str]:
    """Skill names to preload for a stage, with round and cover-letter extras applied."""
    spec = STAGES.get(stage, {})
    rounds = _rounds(round_value)
    out = []
    for name in spec.get("skills", []):
        if name == "<round>":
            out += [ROUND_SKILLS[r] for r in rounds]
        elif name.endswith("*"):
            if TEACHING_ROUNDS & set(rounds):
                out.append(name[:-1])
        else:
            out.append(name)
    if state.get("cover_letter") and "cover_letter" in spec:
        out += spec["cover_letter"]["skills"]
    return list(dict.fromkeys(out))


def _stage_files(stage: str, state: dict) -> list:
    spec = STAGES[stage]
    files = list(spec["files"])
    if state.get("cover_letter") and "cover_letter" in spec:
        files += [f for f in spec["cover_letter"]["files"] if f not in files]
    return files


def _real(entry: str, folder: Path) -> Optional[Path]:
    """Real path for one file entry, or None if it would leave the application folder."""
    if entry == MASTER:
        return config.MASTER_RESUME
    if entry == FACTS:
        return config.CAREER_FACTS
    if entry == LATEST_DRAFT:
        drafts = [(int(m.group(1)), p) for p in folder.glob("tailored_resume_v*.yaml")
                  if (m := re.fullmatch(r"tailored_resume_v(\d+)\.yaml", p.name))]
        return max(drafts)[1] if drafts else None
    path = (folder / entry).resolve()
    return path if path.is_relative_to(folder.resolve()) else None


def _file_section(entry, folder: Path) -> str:
    options = entry if isinstance(entry, tuple) else (entry,)
    paths = [_real(e, folder) for e in options]
    path = next((p for p in paths if p and p.is_file()), None)
    if path is None:
        label = " or ".join(e if e.startswith(("/", "<")) else f"{config.virtual(folder)}/{e}"
                            for e in options)
        return f"----- FILE {label} -----\n(absent)"
    return f"----- FILE {config.virtual(path)} -----\n{path.read_text(encoding='utf-8').rstrip()}"


def _skill_sections(name: str) -> list[str]:
    folder = next((p for p in SKILLS_DIR.glob(f"*/{name}") if (p / "SKILL.md").is_file()), None)
    if folder is None:
        return [f"----- SKILL {name} -----\n(absent)"]
    files = [folder / "SKILL.md"] + sorted(p for p in folder.glob("*.md") if p.name != "SKILL.md")
    return [f"----- SKILL {name}: /skills/{p.relative_to(SKILLS_DIR).as_posix()} -----\n"
            f"{p.read_text(encoding='utf-8').rstrip()}" for p in files]


def load_stage_context(app_dir: str, stage: str, round: Optional[str] = None) -> str:
    """Call this first in every stage. Returns state.json and the folder's file list,
    then every file this stage reads (missing ones marked "(absent)"), then the full
    text of the skills this stage uses. Saves one tool call per file. stage is the
    stage value you were given; for interview prep also pass round (e.g. "technical"
    or "technical-behavioral"). Read anything else you need afterwards."""
    try:
        folder = _app_dir(app_dir)
    except ValueError as exc:
        return f"ERROR: {exc}"
    if not folder.is_dir():
        return f"NOT FOUND: {app_dir}"
    state = _read_state(folder)
    parts = [_summary(folder)]
    if stage not in STAGES:
        parts.append(f"No preset for stage {stage!r}. Read the files and skills you need.")
        return "\n\n".join(parts)
    files = _stage_files(stage, state)
    if not files:
        parts.append(f"No files are preloaded for stage {stage!r}. "
                     "Read only the parts of files this stage needs.")
    parts += [_file_section(entry, folder) for entry in files]
    if stage == "I0_intake" and not _rounds(round):
        parts.append(f"No round skill loaded: round {round!r} is not one of "
                     f"{', '.join(ROUND_SKILLS)}. Load the round skill yourself.")
    for name in stage_skills(stage, state, round):
        parts += _skill_sections(name)
    return "\n\n".join(parts)


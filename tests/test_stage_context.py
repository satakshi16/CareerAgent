"""Tests for load_stage_context and check_draft (performance audit H2)."""
import json
import re

import pytest

from agent import config
from agent.tools import resume_pdf
from agent.tools.stage_context import STAGES, load_stage_context, stage_skills

REAL_ROOT = config.REPO_ROOT
SKILL_DIRS = {p.parent.name for p in (REAL_ROOT / "skills").glob("*/*/SKILL.md")}


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A repo root in tmp_path with one application folder, master resume, and facts."""
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(config, "APPLICATIONS_DIR", tmp_path / "applications")
    (tmp_path / "data").mkdir()
    master = tmp_path / "data" / "master_resume.yaml"
    master.write_text("name: Jordan Lee\n", encoding="utf-8")
    facts = tmp_path / "data" / "career_facts.md"
    facts.write_text("# Career Facts\n- [2026-10-01 | x] Led 4 people (user-confirmed)\n", encoding="utf-8")
    monkeypatch.setattr(config, "MASTER_RESUME", master)
    monkeypatch.setattr(config, "CAREER_FACTS", facts)
    folder = tmp_path / "applications" / "acme_ml-engineer_2026-10-18"
    folder.mkdir(parents=True)
    (folder / "jd.md").write_text("# ML Engineer at Acme\nBuild models.\n", encoding="utf-8")
    (folder / "state.json").write_text(json.dumps(
        {"route": "resume", "stage": "S0_intake", "cover_letter": False}), encoding="utf-8")
    return folder


def _sections(out):
    """Header lines of the returned context, e.g. '----- FILE /applications/x/jd.md -----'."""
    return re.findall(r"^----- (.+?) -----$", out, re.MULTILINE)


def _set_state(folder, **updates):
    state = json.loads((folder / "state.json").read_text())
    state.update(updates)
    (folder / "state.json").write_text(json.dumps(state), encoding="utf-8")


# ---------- load_stage_context ----------

def test_s0_returns_state_files_and_skills_in_one_call(app):
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S0_intake")
    assert out.startswith("app_dir: /applications/acme_ml-engineer_2026-10-18")   # load_application summary
    assert '"stage": "S0_intake"' in out
    heads = _sections(out)
    assert "FILE /applications/acme_ml-engineer_2026-10-18/jd.md" in heads
    assert "FILE /data/master_resume.yaml" in heads and "FILE /data/career_facts.md" in heads
    assert "Build models." in out and "Jordan Lee" in out and "Led 4 people" in out
    assert "SKILL company-research: /skills/shared/company-research/SKILL.md" in heads
    assert "SKILL jd-gap-analysis: /skills/resume/jd-gap-analysis/SKILL.md" in heads
    # Supporting files in a skill folder come along (the gap analysis needs its template).
    assert "SKILL jd-gap-analysis: /skills/resume/jd-gap-analysis/template.md" in heads


def test_missing_files_are_marked_absent(app):
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S1_gap_analysis")
    assert re.search(r"----- FILE /applications/acme_ml-engineer_2026-10-18/gap_analysis.md -----\n\(absent\)", out)


def test_s4_reads_latest_draft_by_number(app):
    for n in (1, 2, 10):
        (app / f"tailored_resume_v{n}.yaml").write_text(f"draft: {n}\n", encoding="utf-8")
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S4_review")
    assert "draft: 10" in out and "draft: 2" not in out and "draft: 1\n" not in out
    assert "cover-letter" not in out


def test_s4_adds_cover_letter_inputs_only_when_requested(app):
    _set_state(app, cover_letter=True)
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S4_review")
    heads = _sections(out)
    assert "SKILL cover-letter: /skills/resume/cover-letter/SKILL.md" in heads
    assert "FILE /applications/acme_ml-engineer_2026-10-18/company_brief.md" in heads


def test_interview_intake_prefers_tailored_resume_and_adds_round_skills(app):
    (app / "tailored_resume_final.yaml").write_text("name: Tailored\n", encoding="utf-8")
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "I0_intake", round="technical")
    heads = _sections(out)
    assert "FILE /applications/acme_ml-engineer_2026-10-18/tailored_resume_final.yaml" in heads
    assert "FILE /data/master_resume.yaml" not in heads
    names = {h.split(":")[0].removeprefix("SKILL ") for h in heads if h.startswith("SKILL")}
    assert {"prep-doc", "technical-round", "explain-simply", "study-resources"} <= names


def test_interview_intake_falls_back_to_master_resume(app):
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "I0_intake", round="behavioral")
    heads = _sections(out)
    assert "FILE /data/master_resume.yaml" in heads
    assert not any("explain-simply" in h or "study-resources" in h for h in heads)
    assert any("behavioral-star" in h for h in heads)


@pytest.mark.parametrize("rnd", ["technical-behavioral", "technical, behavioral", "technical behavioral"])
def test_mixed_round_values(rnd):
    skills = stage_skills("I0_intake", {}, rnd)
    assert "technical-round" in skills and "behavioral-star" in skills


def test_stage_without_preset_files_lists_folder(app):
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "done")
    assert "files: jd.md" in out
    assert "No files are preloaded for stage 'done'" in out


def test_unknown_stage_still_returns_state(app):
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S9_whatever")
    assert '"stage": "S0_intake"' in out
    assert "No preset for stage 'S9_whatever'" in out


def test_bad_app_dir_is_an_error(app):
    assert load_stage_context("/data", "S0_intake").startswith("ERROR")
    assert load_stage_context("/applications/nope", "S0_intake").startswith("NOT FOUND")


def test_app_files_cannot_escape_the_folder(app, monkeypatch):
    monkeypatch.setitem(STAGES, "S_evil", {"files": ["../../data/career_facts.md"], "skills": []})
    out = load_stage_context("/applications/acme_ml-engineer_2026-10-18", "S_evil")
    assert "Led 4 people" not in out


# ---------- the mapping stays in sync with the prompts ----------

def _table_rows(prompt):
    """(stage, skills cell) for each row of the prompt's stage table."""
    text = (REAL_ROOT / "agent" / "prompts" / prompt).read_text(encoding="utf-8")
    lines = [l for l in text.splitlines() if l.startswith("| ")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    col = header.index("Skills")
    rows = []
    for line in lines[2:]:
        cells = [c.strip() for c in line.strip("|").split("|")]
        m = re.match(r"`(\w+)`", cells[0])
        if m:
            rows.append((m.group(1), cells[col]))
    return rows


@pytest.mark.parametrize("prompt", ["resume_tailor.md", "interview_coach.md"])
def test_every_prompt_stage_has_a_preset(prompt):
    rows = _table_rows(prompt)
    assert rows
    assert {stage for stage, _ in rows} <= set(STAGES)


@pytest.mark.parametrize("prompt", ["resume_tailor.md", "interview_coach.md"])
def test_preset_covers_every_skill_the_table_names(prompt):
    all_rounds = "recruiter_screen technical behavioral hiring_manager"
    for stage, cell in _table_rows(prompt):
        named = set(re.findall(r"`([a-z-]+)`", cell)) & SKILL_DIRS
        if not named:
            continue   # "as needed" rows
        loaded = set(stage_skills(stage, {"cover_letter": True}, all_rounds))
        # A row may name skills for one branch only ("as `I0_intake`" etc.); the preset
        # for that stage must still include each one the row names.
        assert named <= loaded, (prompt, stage, named - loaded)


def test_every_preset_skill_exists():
    for stage in STAGES:
        for name in stage_skills(stage, {"cover_letter": True},
                                 "recruiter_screen technical behavioral hiring_manager"):
            assert name in SKILL_DIRS, (stage, name)


# ---------- check_draft ----------

def test_check_draft_runs_both_checks():
    out = resume_pdf.check_draft(config.virtual(config.MASTER_RESUME))
    style, fit = out.split("\n", 1)
    assert style.startswith("STYLE: CLEAN")
    assert fit.startswith("FIT: OK: 1 page")


def test_check_draft_reports_each_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    # Lints (one buzzword) but fails validation (missing required fields).
    (tmp_path / "bad.yaml").write_text(
        "name: X\nsummary: robust\nexperience:\n  - company: A\n    bullets: [Shipped it]\n",
        encoding="utf-8")
    out = resume_pdf.check_draft("/bad.yaml")
    assert "STYLE: 1 violation(s):" in out and "robust" in out
    assert "FIT: ERROR (exit_code 1" in out

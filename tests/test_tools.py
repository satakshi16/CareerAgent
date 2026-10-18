"""Unit tests for the custom tools (instructions.md §13)."""
import json
import shutil
from datetime import date

import pytest
import yaml

from agent import config
from agent.tools import applications, career_facts, resume_pdf, search, style_lint


# ---------- style_lint ----------

def test_lint_catches_em_dash_and_double_hyphen():
    rules = [v["rule"] for v in style_lint.lint("Built a model — fast. Cut cost -- a lot.")]
    assert rules.count("em-dash") == 2


def test_lint_catches_buzzwords_and_inflections():
    found = {v["match"].lower() for v in style_lint.lint(
        "Spearheaded a robust platform and leveraging synergy in a fast-paced environment.")}
    assert {"spearheaded", "robust", "leveraging", "synergy", "fast-paced environment"} <= found


def test_lint_flags_excited_only_as_opener():
    assert style_lint.lint("Excited to apply for this role.")
    assert not style_lint.lint("The team was not excited to see the bill.")


def test_lint_as_a_allowed_once():
    text = "As a manager, I led the work. It shipped. As a data scientist, I built the model."
    hits = [v for v in style_lint.lint(text) if v["rule"] == "as-a-repeat"]
    assert len(hits) == 1


def test_lint_clean_text_and_hyphenated_words():
    assert style_lint.lint("Built a proof-of-concept that cut review time 70%.") == []


def test_lint_master_resume_is_clean_and_ignores_generator_fields():
    # The en dash in "Oct 2022 – Present" style headings and the contact line are
    # generator territory; only content fields are checked.
    assert style_lint.lint(str(config.MASTER_RESUME)) == []


def test_lint_yaml_flags_symbols_in_resume_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    data = yaml.safe_load(config.MASTER_RESUME.read_text(encoding="utf-8"))
    data["summary"] = "Builds models → ships them \U0001F680"
    data["experience"][0]["company"] = "Name — with dash"  # not a content field
    path = tmp_path / "t.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    found = style_lint.lint(str(path))
    assert {v["rule"] for v in found} == {"decorative-symbol", "emoji"}
    assert all(v["field"] == "summary" for v in found)


def test_style_lint_tool_returns_text():
    assert style_lint.style_lint("Plain words.").startswith("CLEAN")
    assert "buzzword" in style_lint.style_lint("A holistic view.")


# ---------- append_career_fact ----------

@pytest.fixture
def facts_file(tmp_path):
    path = tmp_path / "career_facts.md"
    path.write_text("# Career Facts\n\nIntro line.\n", encoding="utf-8")
    return path


def test_append_creates_sections_and_keeps_existing_lines(facts_file):
    day = date(2026, 10, 11)
    before = facts_file.read_text(encoding="utf-8").splitlines()
    sec = "Acme Analytics · Data Science Manager (Oct 2022 – Present)"
    career_facts.add_fact(facts_file, sec, "Agent handles ~4,000 documents/month.", "confirmed", "acme_ml_2026-10-11", day)
    career_facts.add_fact(facts_file, "General / Skills", "Used Databricks on 2 projects.", "confirmed", "acme", day)
    career_facts.add_fact(facts_file, sec, "Number of business units using the churn model", "rejected", "acme", day)
    lines = facts_file.read_text(encoding="utf-8").splitlines()
    assert lines[:len(before)] == before  # append-only: nothing earlier changed
    acme = lines.index(f"## {sec}")
    gen = lines.index("## General / Skills")
    acme_entries = [l for l in lines[acme:gen] if l.startswith("- ")]
    assert acme_entries == [
        "- [2026-10-11 | acme_ml_2026-10-11] Agent handles ~4,000 documents/month. (user-confirmed)",
        "- [2026-10-11 | acme] REJECTED: Number of business units using the churn model. Do not ask again.",
    ]


def test_append_refuses_near_duplicates(facts_file):
    career_facts.add_fact(facts_file, "General / Skills", "Has used Databricks for feature pipelines on 2 client projects.", "confirmed", "a")
    before = facts_file.read_text(encoding="utf-8")
    result = career_facts.add_fact(facts_file, "General / Skills", "Has used Databricks for feature pipelines on two client projects", "confirmed", "b")
    assert result.startswith("REFUSED")
    assert facts_file.read_text(encoding="utf-8") == before


def test_append_rejects_bad_status(facts_file):
    assert career_facts.add_fact(facts_file, "X", "fact", "maybe", "a").startswith("ERROR")


# ---------- validate_resume / render_resume_pdf ----------

def test_validate_master_resume_ok():
    assert resume_pdf.validate_resume(config.virtual(config.MASTER_RESUME)).startswith("OK: 1 page")


def test_validate_reports_broken_yaml(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    (tmp_path / "bad.yaml").write_text("name: X\ncontact: [a]\nsummary: yes\nexperience: oops\n", encoding="utf-8")
    result = resume_pdf.validate_resume("/bad.yaml")
    assert result.startswith("ERROR (exit_code 1")
    assert "line" in result


def test_render_master_resume_one_page(tmp_path, monkeypatch):
    import pdfplumber  # noqa: F401  (dev dependency of the generator)
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(resume_pdf, "APPLICATIONS_DIR", tmp_path / "applications")
    (tmp_path / "applications" / "acme_x_2026-10-11").mkdir(parents=True)
    shutil.copy(config.MASTER_RESUME, tmp_path / "r.yaml")
    monkeypatch.setattr(resume_pdf, "interrupt", lambda payload: "approve")
    result = resume_pdf.render_resume_pdf("/r.yaml", "/applications/acme_x_2026-10-11/Jordan_Lee_Resume_Acme.pdf")
    assert result.startswith("Wrote /applications/acme_x_2026-10-11/Jordan_Lee_Resume_Acme.pdf: 1 page"), result
    with pdfplumber.open(tmp_path / "applications/acme_x_2026-10-11/Jordan_Lee_Resume_Acme.pdf") as pdf:
        assert len(pdf.pages) == 1


def test_render_refuses_output_outside_applications():
    assert resume_pdf.render_resume_pdf(config.virtual(config.MASTER_RESUME), "/data/out.pdf").startswith("ERROR")


SECTIONS = ["contact", "summary", "experience", "education", "skills"]


@pytest.mark.parametrize("reply", ["approve", "Approved.", " yes ", '"approve"', "LGTM",
                                   {"decisions": [{"type": "approve"}]}])
def test_gate_parses_approve(reply):
    assert resume_pdf.parse_decision(reply, SECTIONS) == ("approve", "", "")


def test_gate_parses_reject_with_and_without_reason():
    assert resume_pdf.parse_decision("reject", SECTIONS) == ("reject", "", "")
    assert resume_pdf.parse_decision("Reject: wrong job title", SECTIONS) == ("reject", "", "wrong job title")


def test_gate_parses_edit_and_keeps_colons_in_text():
    assert resume_pdf.parse_decision("edit summary: ML engineer: 6 years", SECTIONS) == (
        "edit", "summary", "ML engineer: 6 years")
    assert resume_pdf.parse_decision("Edit experience / Globex: Cut latency 40%", SECTIONS) == (
        "edit", "experience / Globex", "Cut latency 40%")


@pytest.mark.parametrize("reply", ["edit", "edit summary", "edit: new text", "edit hobbies: chess",
                                   "maybe", 0, None])
def test_gate_returns_hint_for_unclear_reply(reply):
    assert isinstance(resume_pdf.parse_decision(reply, SECTIONS), str)


def _gate(tmp_path, monkeypatch, replies):
    """Run render_resume_pdf with scripted user replies; returns (result, questions asked)."""
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(resume_pdf, "APPLICATIONS_DIR", tmp_path / "applications")
    (tmp_path / "applications" / "acme_x_2026-10-11").mkdir(parents=True)
    shutil.copy(config.MASTER_RESUME, tmp_path / "r.yaml")
    asked, it = [], iter(replies)
    monkeypatch.setattr(resume_pdf, "interrupt", lambda payload: asked.append(payload["question"]) or next(it))
    result = resume_pdf.render_resume_pdf("/r.yaml", "/applications/acme_x_2026-10-11/out.pdf")
    return result, asked


def test_gate_edit_does_not_render(tmp_path, monkeypatch):
    result, _ = _gate(tmp_path, monkeypatch, ["edit skills: Python, SQL"])
    assert result.startswith("EDIT REQUESTED")
    assert "Section: skills" in result and "Python, SQL" in result
    assert not (tmp_path / "applications/acme_x_2026-10-11/out.pdf").exists()


def test_gate_reject_does_not_render(tmp_path, monkeypatch):
    result, _ = _gate(tmp_path, monkeypatch, ["reject: not yet"])
    assert result == "REJECTED by the user. PDF not rendered. Reason: not yet"
    assert not (tmp_path / "applications/acme_x_2026-10-11/out.pdf").exists()


def test_gate_asks_again_after_unclear_reply(tmp_path, monkeypatch):
    result, asked = _gate(tmp_path, monkeypatch, ["approv", "edit hobbies: chess", "reject"])
    assert len(asked) == 3
    assert "didn't understand" in asked[1] and "no section 'hobbies'" in asked[2]
    assert result.startswith("REJECTED")


def test_lint_markdown_file_by_path(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    (tmp_path / "prep.md").write_text("# Prep\n\nI built it — fast.\nA holistic plan.\n", encoding="utf-8")
    found = style_lint.lint("/prep.md")
    assert {v["rule"] for v in found} == {"em-dash", "buzzword"}
    assert all(v["field"] == "/prep.md" for v in found)
    (tmp_path / "ok.md").write_text("Plain words.\n", encoding="utf-8")
    assert style_lint.style_lint("/ok.md").startswith("CLEAN")


# ---------- search ----------

def test_internet_search_passes_include_domains(monkeypatch):
    seen = {}

    class Fake:
        def invoke(self, args):
            seen.update(args)
            return {"results": [{"title": "T", "url": "https://youtube.com/watch?v=1", "content": "c"}]}

    monkeypatch.setattr(search, "_search_client", lambda: Fake())
    out = search.internet_search("rag explained", max_results=3, include_domains=["youtube.com"])
    assert seen["include_domains"] == ["youtube.com"] and seen["max_results"] == 3
    assert "youtube.com/watch" in out
    seen.clear()
    search.internet_search("x")
    assert "include_domains" not in seen


# ---------- applications ----------

@pytest.fixture
def apps_root(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(config, "APPLICATIONS_DIR", tmp_path / "applications")
    return tmp_path / "applications"


def test_create_load_update_application(apps_root):
    out = applications.create_application("Acme Bank", "Senior ML Engineer", "Build models.", True, jd_url="https://x.test/jd")
    assert out.startswith("CREATED")
    folder = apps_root / f"acme-bank_senior-ml-engineer_{date.today().isoformat()}"
    state = json.loads((folder / "state.json").read_text())
    assert state["stage"] == "S0_intake" and state["cover_letter"] is True
    assert state["app_dir"] == f"/applications/{folder.name}"
    assert "https://x.test/jd" in (folder / "jd.md").read_text()

    again = applications.create_application("Acme Bank", "Senior ML Engineer", "Build models.", True)
    assert again.startswith("EXISTS")
    assert applications.create_application("Acme Bank", "Senior ML Engineer", "x", True, reuse_existing=True).startswith("REUSED")

    applications.update_application_state(state["app_dir"], {"stage": "S1_gap_analysis", "completed": ["S0_intake"], "app_dir": "/elsewhere"})
    state = json.loads((folder / "state.json").read_text())
    assert state["stage"] == "S1_gap_analysis" and state["app_dir"] == f"/applications/{folder.name}"
    assert "S1_gap_analysis" in applications.load_application(company="Acme Bank", role="Senior ML Engineer")


def test_create_application_for_interview_route(apps_root):
    applications.create_application("Beta Co", "Data Scientist", "Analyze data.", False, route="interview")
    folder = next(apps_root.glob("beta-co_data-scientist_*"))
    state = json.loads((folder / "state.json").read_text())
    assert state["route"] == "interview" and state["cover_letter"] is False


def test_application_paths_cannot_escape(apps_root):
    assert applications.update_application_state("/data", {"stage": "x"}).startswith("ERROR")
    assert applications.load_application(app_dir="/../../etc").startswith("ERROR")


def test_parallel_appends_keep_every_fact(facts_file):
    from concurrent.futures import ThreadPoolExecutor
    topics = ["Bedrock guardrails", "Hugging Face tokenizers", "PII middleware", "token usage alerts",
              "latency dashboards", "prompt tuning", "conversation state", "Databricks pipelines",
              "Kubernetes deploys", "Snowflake marts", "FastAPI services", "Airflow schedules"]
    facts = [f"Worked with {t} on client project number {i}." for i, t in enumerate(topics)]
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda f: career_facts.add_fact(facts_file, "Sec", f, "confirmed", "a"), facts))
    assert all(r.startswith("Saved") for r in results), results
    text = facts_file.read_text(encoding="utf-8")
    assert all(f in text for f in facts)
    assert not list(facts_file.parent.glob("*.tmp"))


def test_rejected_prefix_not_doubled(facts_file):
    out = career_facts.add_fact(facts_file, "Sec", "REJECTED: Team size on project X", "rejected", "a")
    assert "REJECTED: REJECTED:" not in out and "REJECTED: Team size on project X." in out

"""Run with:  python -m pytest -q"""
import copy
from pathlib import Path

import pytest
import yaml

from resume_generator import template as T
from resume_generator.cli import default_filename, generate, main, resolve_output
from resume_generator.errors import ConfigError, LayoutError, ValidationError
from resume_generator.fonts import load_fonts
from resume_generator.layout import layout_resume
from resume_generator.model import check_glyphs, parse_resume

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "resume.example.yaml"
REFERENCE = ROOT / "reference" / "sample_resume.pdf"


@pytest.fixture(scope="module")
def data():
    return yaml.safe_load(SAMPLE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fonts():
    return load_fonts("liberation")


def write(tmp_path, data, name="r.yaml"):
    p = tmp_path / name
    p.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


def lay(data, fonts, **kw):
    resume, _ = parse_resume(yaml.safe_dump(data, allow_unicode=True))
    check_glyphs(resume, fonts)
    return layout_resume(resume, fonts, **kw)


# ------------------------------------------------------------------ output
def test_sample_fits_one_page_without_adjustment(data, fonts):
    r = lay(data, fonts)
    assert len(r.pages) == 1
    assert (r.extra_scale, r.leading_scale, r.auto_shrink) == (1.0, 1.0, 0.0)


def test_output_is_byte_identical_across_runs(tmp_path):
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    generate(SAMPLE, a, font="liberation")
    generate(SAMPLE, b, font="liberation")
    assert a.read_bytes() == b.read_bytes()
    assert a.read_bytes().startswith(b"%PDF")


def test_matches_reference_line_breaks_and_positions(tmp_path):
    pdfplumber = pytest.importorskip("pdfplumber")
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from compare_reference import extract
    out = tmp_path / "gen.pdf"
    generate(SAMPLE, out, font="liberation")
    gen, ref = extract(out), extract(REFERENCE)
    assert [g["text"] for g in gen] == [r["text"] for r in ref]
    assert max(abs(g["baseline"] - r["baseline"]) for g, r in zip(gen, ref)) < 1.0


# ------------------------------------------------------------ font adjust
@pytest.mark.parametrize("delta", [-1, -0.5, 0, 0.5, 1])
def test_font_adjust_changes_every_role_by_delta(data, fonts, delta):
    r = lay(data, fonts, font_adjust=delta)
    applied = delta + r.auto_shrink
    for role, size in T.SIZES.items():
        assert r.sizes[role] == pytest.approx(size + applied)
    assert len(r.pages) == 1


def test_font_adjust_out_of_range(data, fonts):
    with pytest.raises(LayoutError):
        lay(data, fonts, font_adjust=4)


def test_negative_font_adjust_keeps_original_spacing(data, fonts):
    r = lay(data, fonts, font_adjust=-1)
    assert (r.extra_scale, r.leading_scale, r.auto_shrink) == (1.0, 1.0, 0.0)


# --------------------------------------------------------------- fitting
def test_extra_bullet_is_absorbed_by_spacing(data, fonts):
    d = copy.deepcopy(data)
    d["experience"][0]["bullets"].append("One more short achievement line")
    r = lay(d, fonts)
    assert len(r.pages) == 1 and r.extra_scale < 1.0 and r.auto_shrink == 0


def test_large_overflow_errors_then_paginates_when_allowed(data, fonts):
    d = copy.deepcopy(data)
    d["experience"][0]["bullets"] *= 3
    with pytest.raises(LayoutError, match="overflows"):
        lay(d, fonts)
    r = lay(d, fonts, allow_multipage=True)
    assert len(r.pages) == 2


def test_strict_mode_never_shrinks(data, fonts):
    r = lay(data, fonts, font_adjust=1, strict=False)
    assert r.auto_shrink < 0
    with pytest.raises(LayoutError):
        lay(data, fonts, font_adjust=1, strict=True)


def test_title_colliding_with_dates_is_reported(data, fonts):
    d = copy.deepcopy(data)
    d["experience"][0]["title"] = "Principal " * 12
    with pytest.raises(LayoutError, match="collide"):
        lay(d, fonts)


def test_unbreakable_word_is_split_with_warning(data, fonts):
    d = copy.deepcopy(data)
    d["experience"][2]["bullets"][0] = "See https://example.com/" + "x" * 150
    r = lay(d, fonts)
    assert any("broken mid-word" in w for w in r.warnings)


# ------------------------------------------------------------ validation
def test_missing_and_unknown_fields_reported_together(data):
    d = copy.deepcopy(data)
    del d["summary"]
    d["experience"][0]["titel"] = d["experience"][0].pop("title")
    with pytest.raises(ValidationError) as exc:
        parse_resume(yaml.safe_dump(d))
    msg = str(exc.value)
    assert "summary" in msg and "did you mean 'title'" in msg


def test_boolean_and_bad_url_rejected(data):
    d = copy.deepcopy(data)
    d["experience"][0]["end"] = True
    d["contact"][3]["url"] = "linkedin.com/in/x"
    with pytest.raises(ValidationError) as exc:
        parse_resume(yaml.safe_dump(d))
    assert "boolean" in str(exc.value) and "not a valid link" in str(exc.value)


def test_duplicate_key_detected():
    raw = SAMPLE.read_text(encoding="utf-8").replace(
        "name: JORDAN LEE", "name: JORDAN LEE\nname: Someone Else")
    with pytest.raises(ValidationError, match="more than once"):
        parse_resume(raw)


def test_yaml_syntax_error_has_line_number():
    with pytest.raises(ConfigError, match=r"r\.yaml:\d+:\d+: YAML syntax error"):
        parse_resume("name: a\ncontact: [x\nsummary: y\n", source="r.yaml")


def test_unsupported_character(data, fonts):
    d = copy.deepcopy(data)
    d["summary"] += " \U0001F680"
    resume, _ = parse_resume(yaml.safe_dump(d, allow_unicode=True))
    with pytest.raises(ValidationError, match="U\\+1F680"):
        check_glyphs(resume, fonts)


def test_whitespace_normalized_and_invisibles_removed(data):
    d = copy.deepcopy(data)
    d["summary"] = "Line one\n\n   line\u00adtwo\u200b"
    resume, warnings = parse_resume(yaml.safe_dump(d, allow_unicode=True))
    assert resume.summary == "Line one linetwo"
    assert len(warnings) == 2


def test_numbers_and_dates_coerced(data):
    d = copy.deepcopy(data)
    d["contact"][1] = 5550100199
    resume, warnings = parse_resume(
        yaml.safe_dump(d).replace("date: May 2017", "date: 2017-05-01"))
    assert resume.contact[1].text == "5550100199"
    assert resume.education[0].date == "2017-05-01" and warnings


def test_skill_items_list_joined(data):
    d = copy.deepcopy(data)
    d["skills"][0]["items"] = ["Python", "SQL"]
    resume, _ = parse_resume(yaml.safe_dump(d))
    assert resume.skills[0].items == "Python, SQL"


# ------------------------------------------------------------------- CLI
def test_default_and_custom_filenames(tmp_path):
    assert default_filename("JORDAN LEE") == "JORDAN_LEE_Resume.pdf"
    assert resolve_output(None, "A B").name == "A_B_Resume.pdf"
    assert resolve_output(str(tmp_path / "cv"), "A").name == "cv.pdf"
    assert resolve_output(str(tmp_path), "A B") == tmp_path / "A_B_Resume.pdf"


def test_cli_exit_codes(tmp_path, data, capsys):
    assert main([str(SAMPLE), "-o", str(tmp_path / "x.pdf"), "--font", "liberation", "-q"]) == 0
    assert (tmp_path / "x.pdf").exists()
    assert main([str(tmp_path / "nope.yaml")]) == 1
    d = copy.deepcopy(data)
    d["experience"][0]["bullets"] *= 3
    assert main([str(write(tmp_path, d)), "--check"]) == 3
    with pytest.raises(SystemExit) as exc:
        main([str(SAMPLE), "--font-adjust=9"])
    assert exc.value.code == 2

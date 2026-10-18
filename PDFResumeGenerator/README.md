# Resume PDF Generator

A deterministic, offline generator that turns `resume.yaml` into a PDF with a
fixed, single-page layout (see `reference/sample_resume.pdf`).
The design is fixed in code; you update your resume by editing the YAML only.

No network access, no AI/LLM calls at runtime. The same YAML always
produces a byte-identical PDF, in about 40 ms.

## Setup

Requires Python 3.9 or newer.

```bash
cd resume-pdf-generator
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # reportlab + PyYAML
cp resume.example.yaml resume.yaml # then replace the sample content with yours
```

`resume.yaml` holds personal data and is gitignored. `resume.example.yaml` is a
fictional sample, and the tests use it.

## Usage

```bash
python generate_resume.py                          # resume.yaml -> <NAME>_Resume.pdf
python generate_resume.py -o my_resume.pdf         # custom filename (".pdf" added if missing)
python generate_resume.py -o out/                  # default filename inside a folder
python generate_resume.py other.yaml               # a different content file
python generate_resume.py --font-adjust=+1         # all text 1 pt larger
python generate_resume.py -f -1                    # all text 1 pt smaller
python generate_resume.py --check                  # validate + lay out, write nothing
```

| Option | Meaning |
|---|---|
| `config` | Content file (default `resume.yaml`). |
| `-o, --output` | Output file or folder. Default: `<Name>_-_Resume.pdf` in the current folder. |
| `-f, --font-adjust PT` | Adds `PT` points to every text size (body, section headers, subsections, name, contact). Range −3 to +3; fractions like `-0.5` work. Write negatives as `--font-adjust=-1` or `-f -1`. |
| `--font auto\|arial\|liberation` | `auto` (default) uses Arial if installed, else the bundled Liberation Sans. |
| `--strict` | Never auto-shrink text to fit; fail instead. |
| `--allow-multipage` | If content cannot fit one page, continue onto page 2 instead of failing. |
| `--check` | Validate and report fit without writing a PDF. |
| `-q, --quiet` | Print errors only. |

Exit codes: `0` success, `1` content/YAML problem, `2` bad command-line option,
`3` layout problem (overflow, collision), `4` font or file-write problem.

## Updating your resume (YAML only)

Open `resume.yaml`, edit, and re-run the command. Things you can change:

- Any text: name, contact items, summary, titles, dates, bullets, schools, skills.
- The number and order of jobs, bullets, schools, and skill lines.
- Contact items: plain text, or `{text: ..., url: ...}` for a blue underlined link.
- `location` is optional for jobs and schools (the " – City" part is dropped).
- Skill `items` may be one string or a list (a list is joined with ", ").

The program adds all decoration itself: the en dash between company and
city, the " – " between start and end dates, the " | " between contact items,
the colon after skill labels, the bullet dots, section titles and rules.

YAML tips:

- Quote values containing `: ` or starting with a special character, e.g. `"P: +1 848..."`.
  Quoting is always safe.
- Long text can use `>` and continue on indented lines; line breaks become spaces.
- Unquoted `yes`, `no`, `on`, `off` are booleans in YAML and are rejected; quote them.
- The file must be saved as UTF-8.

## How the reference PDF became the template

The reference was analyzed once, during development, and every measurement
was hard-coded in `resume_generator/template.py`. That file is the only place
visual design lives.

The original reference is the author's own resume and is not in the repo. The
committed `reference/sample_resume.pdf` is rendered from `resume.example.yaml`
and is the regression baseline: the unit test and `tools/compare_reference.py`
check that layout changes don't move any line. If you change the layout on
purpose, regenerate it with
`python generate_resume.py resume.example.yaml -o reference/sample_resume.pdf --font liberation`.

1. **Page and margins.** `pdfinfo` gave US Letter (612×792 pt), one page.
   Character boxes from `pdfplumber` showed every left-aligned line starting at
   x = 43.92 and right-aligned dates ending at 568.06, i.e. 0.61 in margins.
2. **Fonts and colors.** `pdffonts` and per-character font data showed the Arial
   family: name 16.08 pt bold, contact and section headers 10.56 pt,
   body/subsections 10.08 pt. Fill colors gave gray `#404040` for the name,
   headers and employer/school lines, and Word's link blue `#0563C1`.
3. **Vertical rhythm.** Baselines were read from each line's text matrix. Body
   line pitch is exactly 11.52 pt (8/7 × 10.08). Every other spacing (name to
   contact, header to first entry, bullet to bullet, entry to entry, and so on)
   was recorded as a baseline-to-baseline distance in `GAPS`.
4. **Rules, bullets, links.** Filled rectangles gave the 0.72 pt section rules
   (3.12 pt below the header baseline, overhanging the text by 1.44 pt) and link
   underlines. The Symbol-font bullet was rasterized at 1200 dpi to measure the
   dot (3.6 pt diameter); it is drawn as a vector circle, so it looks the same
   with any font. Link annotations gave the clickable areas.
5. **Word's text grid.** Comparing roughly 3,400 character advances against Arial's
   metrics showed that Word laid glyphs out as if at 10.0 / 10.5 / 16.0 pt while
   drawing them at 10.08 / 10.56 / 16.08 pt. This 0.5–0.8% tightening decides
   which word ends each line, so it is reproduced (`ADVANCE_SIZES`) with a
   matching PDF horizontal text scale. Word-compatible wrapping (breaking after
   spaces and after hyphens, as in "proof-of-/concept") completes the match.

The result, checked by `tools/compare_reference.py` and a unit test: all 52
lines break on exactly the same words as the reference, baselines are within
1 pt, and x positions are within 0.7 pt. Three deliberate normalizations of
inconsistencies in the Word original account for the remaining differences.
One "|" separator was set in Calibri 12 pt, and the Arial version shifts the
contact line by about 2 pt. Some bullets were indented 0.7 pt differently from
others, and are now uniform. Word's pixel snapping made some gaps vary by
±0.24 pt, and each gap now uses one consistent value.

### Fonts

Arial cannot be redistributed, so `fonts/` bundles **Liberation Sans**
(SIL Open Font License, see `fonts/LICENSE-LiberationSans.txt`). It was
designed to be metrically identical to Arial: every character has the same
width. Layout, line breaks and page fit are therefore identical whether
Arial or Liberation Sans is used; only fine glyph details differ. Use
`--font liberation` for output that is identical on every machine, or
`--font arial` to require the real Arial (found automatically on macOS,
Windows, and Linux with `ttf-mscorefonts`).

## Keeping to one page

The reference fills its page, so added content needs room. The generator
tries these settings in order and uses the first that fits:

1. Natural reference spacing.
2. Compress the space between sections, entries and bullets, down to 60%.
3. Reduce line spacing slightly (down to 95%, about 1.09× line height).
4. Compress the space between blocks further, down to 50%.
5. Shrink all text by 0.1 pt steps, up to 0.5 pt. `--strict` skips this step.

Any adjustment is reported, for example
`fitted to page: section/entry spacing at 85%`. If nothing fits, the program
stops with the overflow size ("overflows 1 page by 14.2 pt (about 2 lines)")
unless `--allow-multipage` is given. With that option, pages break between
bullets, and headers stay with their first entry. Smaller content is never
stretched; it keeps the reference spacing.

A positive `--font-adjust` on a full page will usually trigger this fitting.
For example, `+1` fits the sample by compressing spacing and trimming 0.2 pt.

## Validation

All problems are reported together, with YAML line numbers:

- YAML syntax errors, with line and column.
- Missing required fields, unknown fields (with "did you mean" hints) and duplicate keys.
- Wrong types, such as a list where text is expected.
- Booleans where text is expected. Unquoted numbers and dates are converted to text with a warning.
- Invalid URLs (links must start with `https://`, `http://` or `mailto:`).
- Control characters. Tabs and newlines are normalized, and invisible characters (soft hyphens, zero-width spaces, BOM) are removed with a warning.
- Characters missing from the font, such as emoji, with their code points.
- Lines that cannot wrap and are too long, such as a job title that would collide with its dates, or a name wider than the page.
- A single word wider than the line, such as a long URL, is broken mid-word with a warning.
- Page overflow, as described above.
- Output problems, such as an unwritable path or a PDF open in a viewer on Windows. Writes are atomic, so a failure never leaves a half-written PDF.

## Project layout

```
resume-pdf-generator/
├── generate_resume.py        # entry point
├── resume.yaml               # YOUR CONTENT (the only file to edit, gitignored)
├── resume.example.yaml       # fictional sample, used by the tests
├── requirements.txt          # runtime: reportlab, PyYAML
├── requirements-dev.txt      # + pytest, pdfplumber
├── resume_generator/
│   ├── template.py           # all measurements from the reference (design)
│   ├── model.py              # YAML loading + validation -> dataclasses
│   ├── layout.py             # wrapping, placement, fit-to-page
│   ├── render.py             # ReportLab drawing, atomic write
│   ├── fonts.py              # Arial / Liberation Sans resolution
│   ├── cli.py                # command-line interface
│   └── errors.py
├── fonts/                    # Liberation Sans + license
├── reference/                # sample_resume.pdf, rendered from resume.example.yaml
├── tools/compare_reference.py# line-by-line fidelity report vs the reference
└── tests/test_generator.py
```

## Development

```bash
pip install -r requirements-dev.txt
python -m pytest -q                                   # 25 tests
python generate_resume.py -o out.pdf --font liberation
python tools/compare_reference.py out.pdf             # fidelity report
```

`python -m resume_generator` also works as an entry point. For use from other
Python code, call `from resume_generator import generate`.

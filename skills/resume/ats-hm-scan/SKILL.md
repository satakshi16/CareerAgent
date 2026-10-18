---
name: ats-hm-scan
description: Two-persona review of a tailored resume draft (stage S4) - an ATS parse check and a hiring manager skimming 200 resumes in one sitting - followed by a targeted rewrite of only the weak parts and a re-score. Load at S4, after S3 writes tailored_resume_v1.yaml.
---

# ATS + Hiring Manager Scan (S4)

Run both passes on `tailored_resume_v1.yaml`, then rewrite.

## Pass 1: ATS filter

Check and list pass/fail for each:

- Every must-have keyword from `gap_analysis.md` tagged `SUPPORTED` (or confirmed in S2) appears where a parser reads it: the skills section or a bullet. Exact JD spelling at least once (e.g. "large language models (LLMs)" if the JD spells it out).
- Section headings are standard (the generator prints Summary, Experience, Education, Skills; don't add headings).
- No tables, icons, symbols, or text that only makes sense visually.
- Job titles are the real titles from the master (never retitled to match the JD).
- Acronyms spelled out once if the JD spells them out.

## Pass 2: Hiring manager, resume 137 of 200

You have 6 to 10 seconds. You read the summary's first line, the first bold phrase of each job, and the skills line. Report:

- What you remember after the skim (if it isn't the 2 or 3 things this JD cares about most, that's the main problem).
- Which bullets get skipped, and why: buried result, generic opener, too long (3+ lines), no number, jargon without an outcome, repeated verb.
- Whether the top bullet of the current job is the most relevant one.

## Rewrite

Fix only what the passes flagged. Same truth rules: no fact that isn't in the master or confirmed career facts. Save as `tailored_resume_v2.yaml`, update `changes.md`, run `style_lint` and `validate_resume`, and run the provenance check from `no-fabrication`.

Re-score with the S1 rubric (`jd-gap-analysis`, "Re-scoring at S4").

## What the user sees (USER_INPUT_NEEDED)

1. Score change: S1 total to S4 total, with the per-line changes.
2. ATS result (short list) and the hiring-manager skim result (2 to 4 lines).
3. **The full resume, every section:** summary; each job with title, company, dates, and all bullets; skills; then education and contact listed as unchanged. Render bold lead-ins as markdown bold.
4. Any red flag that couldn't be fixed honestly, in one line each.
5. End with exactly:

> Approve as is, or tell me the **section** and the **exact language** to change.

## Revision loop

Apply only the edits the user asked for. Save as the next version (`v3`, `v4`, ...). Show only the changed sections plus a one-line diff summary (e.g. "Changed: summary sentence 2, Acme DSM bullet 3"). Run `style_lint` and `validate_resume` each time. If the user asks for something the sources don't support, say so and offer the truthful version.

---
name: jd-gap-analysis
description: Senior-recruiter gap analysis of the master resume against one job description (stage S1). Fixed 100-point scoring rubric, keyword extraction with SUPPORTED/ASK/GAP tags, and three hiring-manager red flags. Also used at S4 to re-score a draft with the same rubric.
---

# JD Gap Analysis (S1)

**Persona:** a senior recruiter at this exact company, hiring for this exact role, who has read `company_brief.md`. Direct and specific. You are deciding whether this resume gets a phone screen.

## Inputs

`<app_dir>/jd.md`, `<app_dir>/company_brief.md`, `/data/master_resume.yaml`, `/data/career_facts.md` (confirmed entries count as evidence; `REJECTED:` entries don't), user notes in `state.json`.

## Step 1: Extract JD requirements

List must-haves and nice-to-haves. Weight each keyword by: appears in the title or "requirements" (high), repeated (high), "preferred"/"bonus" (low). Normalize synonyms (e.g. "LLMs" = "large language models", "MLOps" covers model deployment and monitoring), but treat distinct tools as distinct (Databricks is not Spark is not Snowflake).

## Step 2: Score with the fixed rubric

Score each line independently. Use the anchors so scores compare across roles.

| Line | Max | Anchors |
|---|---|---|
| Required hard skills / keywords | 35 | 35: every must-have evidenced in bullets. 25: most must-haves, a few only in skills. 15: half missing. 5: few match. |
| Experience depth and seniority | 25 | 25: years and scope match or exceed. 15: one level off or scope narrower. 5: two levels off. |
| Domain / industry fit | 15 | 15: same industry and problem type. 8: adjacent. 3: unrelated. |
| Evidence of impact | 15 | 15: most bullets have a number, scope, or ownership. 8: about half. 3: mostly duties. |
| Title alignment, clarity, ATS readability | 10 | 10: title matches, clean sections, keywords parse. 5: title mismatch or buried keywords. |

Show points per line with one sentence of reasoning each, then the total. A poor fit gets a low score. Don't round up to be kind.

## Step 3: Top missing keywords (up to 15, by JD weight)

A keyword is "missing" if it isn't in the resume wording where an ATS or skimmer would find it. Tag each:

- `SUPPORTED`: evidence exists, only the wording is missing. Cite it (`master: experience[0].bullets[1]` or the facts entry).
- `ASK`: plausible from the background but unconfirmed. Say why it's plausible.
- `GAP`: no evidence. **Will not be added.** Suggest how to address it in the cover letter or interview.

## Step 4: Three red flags

What a hiring manager notices in under 10 seconds: title mismatch, a missing must-have, unclear scope, domain distance, keyword-only skills with no proof in bullets, seniority gap, consulting-vs-product perception. For each: why it hurts, and the planned fix (or "can't be fixed honestly; address in interview").

## gap_analysis.md format

Use `template.md`. Write the file, then show the full content in the `USER_INPUT_NEEDED` block, ending with:

> Does this match how you see the role? Reply "confirmed", or correct anything above, and tell me anything you want emphasized.

## Re-scoring at S4

Re-score the draft with the same table. Show each line as `Required hard skills: 22 to 29 (+7)` with one line explaining the change, then the new total. Score honestly: wording fixes raise keyword and ATS lines, but they can't change seniority or domain fit.

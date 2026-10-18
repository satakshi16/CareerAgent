---
name: no-fabrication
description: Truth rules and the provenance check for anything said about the candidate. Load before writing or revising resume content, cover letters, or interview answers, and before showing a draft for approval (S4) or rendering the PDF (S5).
---

# Truth & No-Fabrication

## Allowed sources (nothing else)

1. `/data/master_resume.yaml`
2. Confirmed entries in `/data/career_facts.md` (lines without `REJECTED:`)
3. What the user says in the current thread, **after** it has been saved with `append_career_fact`

Web research is context about the company. It is never evidence about the candidate.

## Never

- Invent or inflate metrics, tools, team sizes, employers, titles, dates, degrees, certifications, clients, or outcomes.
- Merge two projects into one, or move a result from one job to another.
- Upgrade the verb: "contributed to" can't become "led"; "built a POC" can't become "deployed to production"; "projected to save $1.5M" can't become "saved $1.5M".
- Use a `REJECTED:` metric, or ask for it again.
- Add a JD keyword with no evidence. That is a `GAP`. Keep it out of the resume and address it in the cover letter or interview.

Rewording is fine. Changing meaning is not. Hedged claims stay hedged ("projected", "estimated", "proof of concept").

## Provenance check (before S4 is shown and before S5)

For every summary sentence, every bullet, and every skills item in the draft:

1. Find its source: a master line (cite as `master: experience[0].bullets[2]`, `master: summary`, `master: skills[2]`) or a fact entry (cite as `facts: [2026-10-11 | app] first words...`).
2. Check every number, tool, and scope word in the line against that source.
3. Record it in the `source` column of `changes.md`.
4. A line with no source, or with a detail the source doesn't support, is removed or becomes a question for the user. Never ship it.

Report the result in the stage header: `Provenance: N lines checked, all sourced` or list what was removed.

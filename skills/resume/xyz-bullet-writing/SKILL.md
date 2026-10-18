---
name: xyz-bullet-writing
description: How to rewrite the summary, experience bullets, and technical skills for one JD (stage S3) using the Google XYZ formula, bold result lead-ins, natural keyword placement, and relevance ordering. Also produces changes.md. Load at S3 and for any S4 rewrite of a weak line.
---

# XYZ Bullet Writing (S3)

Load `no-fabrication`, `human-writing`, and `resume-yaml-format` alongside this skill.

## Inputs

Master resume, confirmed career facts, `gap_analysis.md` (keywords + red flags), `elicitation.md` (user direction), `company_brief.md` (for the summary angle only).

## Bullets

**Formula:** accomplished [X], as measured by [Y], by doing [Z].

**Shape:** start with a short **bold result phrase** (3 to 9 words, the X and Y), then how (Z). Keep each bullet to about 2 lines on the page (roughly 200 to 260 characters). Examples of the shape, built only from master facts:

- `"**Cut manual policy review by 50%** while keeping precision above 90%, by building a text classifier that flags insurance claims needing a second look"`
- `"**96% classification and 89% extraction accuracy** on a 300-document invoice test set. Led a 3-person team building a reusable invoice-processing agent on LangGraph with configurable fields"`
- When there is no number, lead with scope or ownership: `"**Led a 6-person onshore/offshore team** testing single- vs multi-agent designs for a customer-support assistant..."`

Rules:

- One JD keyword per bullet at most, only where the source supports it, worded the way the JD words it.
- Fix each S1 red flag, or note in `changes.md` why it can't be fixed honestly.
- Within each job, order bullets by relevance to this JD. Cut the least relevant if space is needed. Never invent a bullet, and never move a result to a different job.
- No first person. Past tense for past roles; present tense is fine for the current role.
- Keep hedges from the source ("projected", "proof of concept").

## Summary

2 to 3 sentences. Open with the identity that matches the JD title, only if true (a Data Science Manager can open as "Data scientist and ML lead", not "ML Engineer" unless the evidence supports engineering work). Then the 2 strongest proof points for this JD, then scope (team, domain). No buzzwords, no "seeking", no objective statement.

## Skills

Keep the master's labels unless a relabel helps the ATS (e.g. "LLM / GenAI" to "LLMs & Agents"). Put the JD's must-have tools first in each line. Add a JD term **only** if the master or a confirmed fact shows the candidate has it. Remove items that are irrelevant and cost space.

## changes.md

```markdown
# Changes: <Role> at <Company>

| Section | Original | New | Source | Keywords added |
|---|---|---|---|---|
| summary | <old sentence> | <new sentence> | master: summary | LLM agents |
| Acme DSM bullet 1 | <old> | <new> | master: experience[0].bullets[0]; facts: [2026-10-11 | ...] | evaluation |
| skills: LLM / GenAI | <old> | <new> | master: skills[2] | ... |

## Cut
- <bullet> (reason)

## Red flags
1. <flag>: fixed by ... / not fixable honestly because ...
```

Every new line needs a source. Unchanged lines can be listed as "unchanged".

## Before moving on

1. `style_lint <draft path>` returns CLEAN.
2. `validate_resume <draft path>` returns OK (fits one page). If it overflows, cut the least relevant bullet and try again.

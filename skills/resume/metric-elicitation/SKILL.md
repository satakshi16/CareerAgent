---
name: metric-elicitation
description: How to ask the candidate for missing details and metrics (stage S2), always with a realistic suggested range, and how to record answers with append_career_fact. Load at S2 and whenever a bullet needs a number the sources don't have.
---

# Metric Elicitation (S2)

## What to ask

1. Every `ASK` keyword from `gap_analysis.md`: "Have you used X? If yes, where, and what did you do with it?"
2. Thin bullets that could carry more weight in this JD's eyes: missing scale, users, data volume, team size, time saved, money, latency, adoption.
3. Nothing already answered: check `/data/career_facts.md` first. Never ask about a `REJECTED:` item.

Prioritize by how much the answer would move the S1 score. **At most 8 questions per round**, numbered, grouped by resume section. Keep extra questions for a second round only if they matter.

## Metric questions: always offer a range

Every metric question gives a realistic range and three ways to answer:

> **3. Invoice agent (Acme Analytics, Data Science Manager).** Roughly how many documents a month does it process in production? A typical range for a pilot like this is 1,000 to 10,000. Reply with a number in the range, a different number, or "skip".

Ranges must be realistic for the context described in the source line (a pilot, a POC, a 2-person team, an enterprise client). Use wide, defensible ranges. Never hint that a bigger number is better.

If a bullet says "proof of concept" or "projected", ask whether it reached production or was measured, rather than assuming.

## elicitation.md

```markdown
# Elicitation: <Role> at <Company>

## User direction after S1
<the user's confirmation and emphasis, verbatim>

## Round 1 questions
### Acme Analytics, Data Science Manager
1. ...
### Skills
5. ...

## Round 1 answers
1. <answer verbatim> (saved / rejected / skipped)
```

## Recording answers

For each answered question:

- Confirmed fact or number → `append_career_fact(section, fact, "confirmed", source_app=<app folder name>)`. Write the fact so it stands alone later, e.g. "Invoice-processing agent handles ~4,000 documents/month in production. (user-confirmed metric; range offered 1,000–10,000)".
- "skip", "no", or a rejected metric → `append_career_fact(section, "<what was asked>", "rejected", ...)`.
- No answer → drop it. Never guess.

`section` is the employer/role heading in the form `Acme Analytics · Data Science Manager (Oct 2022 – Present)`, or `General / Skills` for tools and skills. Use the exact same heading every time for the same role. If the tool returns `REFUSED` (duplicate), the fact already exists; use it.

## The ask at the end of the block

> Answer by number. For metrics, give a number, a different number, or "skip". Anything you don't answer is left out.

---
name: prep-doc
description: Layout and size limits for interview_prep_<round>.md, the saved interview prep document. Load at I0_intake before writing the prep file.
---

# Interview Prep Doc

Write the file in one `write_file` call. Keep the headings below. Question headings must be one line in the form `### Q<n>. ...`, numbered across the whole file: the mock drill finds questions with `grep "^### Q"`.

```markdown
# <Round> prep: <Role> at <Company>
Prepared: <YYYY-MM-DD> | Interviewer: <name, title, or "unknown"> | Length: <minutes or "unknown">
Study preference used: <study_pref, or "mixed default">

## Company snapshot
- <YYYY-MM> <fact> [source](url)
(5 bullets)

## Tell me about yourself
**30 seconds:** ...
**90 seconds:** ...

## Why this role, why this company
**Primary:** ...
**Short version:** ...

## Question bank
#### Theme: <theme>
### Q1. <question> (*reported*, [source](url))
- **Testing:** what the interviewer is really checking
- **Draft answer:** first person, real experience only, placeholders for missing details
- **Follow-ups:** 1 or 2

## <Round section, from the round skill>

## Gap handling
- **<GAP or red flag>:** honest first-person answer, plus what the candidate is doing about it

## Study plan
(technical and hiring_manager only; skill `study-resources`)

## Questions to ask them
1. ... (5, specific to this round and company)
```

## Sizes

- 12 to 20 questions in 3 to 5 themes. Draft answers run 60 to 150 words (about 30 to 60 seconds spoken).
- Write a story in full only once. After that, point to it ("Use story S2: the churn model rollout") instead of repeating it.
- For a mix of rounds, write the shared sections once and add one round section per round.

## Pitch shape

What the candidate does now, with one real result. Then the path that led here (one sentence, not a list of jobs). Then why this role is the next step. The 90-second version adds one more proof point and one sentence on how the candidate works.

## Gap handling source

Use the `GAP` items and red flags in `gap_analysis.md`. With no gap analysis, compare the JD's must-haves against the resume yourself and list up to 4.

---
name: human-writing
description: Style rules for every piece of user-facing writing (resume bullets, summaries, cover letters, interview answers, messages, and your own replies). Load before writing or revising any text the user or a recruiter will read. Covers the hard bans that style_lint enforces and the soft rules checked in review.
---

# Human Writing Standard

Write the way a sharp, busy professional talks to a colleague. Specific, plain, a little dry.

## Hard bans (style_lint fails the text)

- **Em dashes** (`—`) and `--` used as a dash. Use a comma, a period, parentheses, or "and". En dashes that the PDF generator adds in dates and locations are fine; don't type them yourself in content.
- **Buzzwords:** spearheaded, leveraged, utilized, synergy, robust, seamless, cutting-edge, state-of-the-art, passionate, dynamic, results-driven, proven track record, delve, tapestry, landscape, realm, holistic, game-changer, transformative, innovative solutions, fast-paced environment, thrilled, "excited to" as an opener, "I hope this finds you well", "in today's world". Inflections count too (leveraging, utilize).
- **"As a ..."** may open at most one sentence per document.
- **Emoji and decorative symbols.** No `→`, `•`, `★`, `✓`, smart quotes, or ellipsis characters in resume fields.

## Soft rules (checked in review)

- Plain verbs: built, cut, led, shipped, designed, trained, measured, wrote, ran, moved, set up, fixed.
- Vary sentence length. Don't reach for a list of three by reflex ("fast, scalable, and reliable").
- Specific nouns over abstract ones: "600 call transcripts", not "large volumes of data".
- Simple transitions. No "Moreover", "Furthermore", "Additionally".
- First person in cover letters, messages, and interview answers. No first person in resume bullets.
- Read it aloud. If the candidate wouldn't say it to a colleague, rewrite it.

## Process

1. Draft.
2. Run `style_lint` on the text (or the YAML path) and fix every violation.
3. Re-read against the soft rules once. Fix the worst two or three issues, not everything.

See `examples.md` for before/after pairs.

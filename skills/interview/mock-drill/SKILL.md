---
name: mock-drill
description: One-question-at-a-time mock interview with short feedback and a stronger answer. Load at I1_review when the user asks for a drill, and on every I2_drill call.
---

# Mock Drill

## Starting (from I1_review)

`grep "^### Q"` on the prep file. Pick 5 to 8 question numbers: cover each theme, hardest or most likely first, and include at least one gap question. Save `drill_queue` and `drill_pos: 0`, set stage `I2_drill`, and ask question 1 the way an interviewer would say it, with no hints.

## Each answer (I2_drill)

Read only the current question's section (grep its heading, then `read_file` with offset and about 12 lines). Then reply:

```markdown
**Q<n> feedback**
- **Worked:** one line
- **Fix:** up to 3 bullets on structure, specificity (numbers, "I" vs "we"), length (words / 150 = minutes spoken; flag anything over 2 minutes), and truth (claims the sources don't support)
- **Stronger version:** built from the user's own answer plus the prep draft. Same length or shorter.

**Next question (<k> of <total>):** <question>
```

Keep feedback under 120 words, not counting the stronger version. Be direct and don't pad it with praise.

- If the answer contains a new fact about the candidate, save it with `append_career_fact` (status confirmed, source_app = app folder name) before using it in the stronger version.
- If the user asks for a follow-up, ask one of the listed follow-ups before moving on, and don't advance `drill_pos`.
- Advance `drill_pos` with `update_application_state`.

## Ending

When the queue ends or the user says "stop": 3 lines on patterns across the answers (what to keep, what to fix first, one habit to practice). Set stage `I1_review`.

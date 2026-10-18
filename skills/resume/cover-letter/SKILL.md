---
name: cover-letter
description: Structure and limits for a short, specific cover letter (stage S6), built from the final resume and company_brief.md. Shown in chat only, never saved to a file. Load at S6 when state.json has cover_letter true, or when the user asks for a cover letter later.
---

# Cover Letter (S6)

Load `human-writing` and `no-fabrication` too.

## Inputs

`tailored_resume_final.yaml`, `company_brief.md` (the "Hooks" section), `gap_analysis.md` (GAP items), `jd.md` (top 2 or 3 needs).

## Limits

- 200 to 280 words. 3 to 4 short paragraphs. First person.
- Count the words before showing it and print the count under the letter.

## Structure

1. **Connect (2 to 3 sentences).** Open with a specific, recent thing about the company or team from `company_brief.md` and why it connects to the candidate's work. Never "I am writing to apply", never "I am excited to".
2. **Proof (one paragraph, sometimes two).** One or two results from the final resume, each tied to one of the JD's top needs. Use the same numbers as the resume, no new ones.
3. **Gap (optional, 1 to 2 sentences).** Address one `GAP` honestly if it helps: what the candidate has that's adjacent, and how they're closing it, only with real evidence. Skip it if there's nothing true to say.
4. **Close (1 to 2 sentences).** A plain call to action: "I'd welcome a conversation about ..." Then "Best regards," and the candidate's full name from the master resume.

## Output

Put the letter inside the `=== FINAL ===` block under a "Cover letter" heading, followed by `Word count: N`. Run `style_lint` on the letter text first. Do not write it to any file.

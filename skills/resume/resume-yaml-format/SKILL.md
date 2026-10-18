---
name: resume-yaml-format
description: The tailored resume YAML schema and the PDFResumeGenerator rules (bold markup, quoting, separators, plain characters, one page). Load whenever you write or edit a tailored_resume_*.yaml file, and when validate_resume returns errors.
---

# Resume YAML Format

Tailored files use the same schema as `/data/master_resume.yaml`. Start every new draft by copying the master's structure, then change only content fields.

## Schema

```yaml
name: JORDAN LEE                      # copy from master
contact:                              # copy from master, unchanged
  - Austin, TX
  - "P: +1 555 010 0199"
  - jordan.lee@example.com
  - text: LinkedIn Profile
    url: https://www.linkedin.com/in/example/
  - text: GitHub
    url: https://github.com/example
summary: >                            # rewritable
  ...
experience:
  - company: Acme Analytics           # copy
    location: Austin, TX              # copy (optional field)
    title: Data Science Manager       # copy, never retitle
    start: Oct 2022                   # copy
    end: Present                      # copy
    bullets:                          # rewritable, reorderable, cuttable
      - "**Bold result phrase** then how it was done"
education:                            # copy, unchanged
  - school: ...
    location: ...
    date: May 2017
    degree: ...
skills:                               # rewritable (only true skills)
  - label: LLM / GenAI
    items: LangGraph, LangSmith, RAG (FAISS), LLM fine-tuning (LoRA)
```

`headline` (optional, plain text) exists but is unused in the master. Don't add it unless the user asks.

## Rules

- **Bold:** `**...**` works only in `summary`, bullets, education `degree`, and skills `items`. Pairs must match. A value that **starts** with `**` must be in double quotes or use `>` folded style. Easiest: double-quote every bullet.
- **Quoting:** quote any value containing `: ` or starting with a special character. Unquoted `yes`, `no`, `on`, `off` are rejected. Inside double quotes, escape `"` as `\"`.
- **Separators:** don't type them. The generator adds the en dash between company and city, the dates dash, ` | ` between contact items, the colon after skill labels, and bullet dots. Don't start bullets with `-` or `•` inside the text.
- **Plain characters only:** no emoji, no smart quotes, no `→`, no invisible characters. Use straight quotes and `%`, `$`, `+`, `/`, `&`.
- **One page:** the generator compresses spacing and can shrink text by up to 0.5 pt. Beyond that you must cut content. Each bullet is about 2 lines; cutting one bullet frees about 2 lines.

## Workflow

1. Write the file with `write_file` to `<app_dir>/tailored_resume_vN.yaml`. Never overwrite an earlier version.
2. `validate_resume("<app_dir>/tailored_resume_vN.yaml")`.
3. On `ERROR`, read the listed YAML line numbers, fix, write the file again under the same version name (it hasn't been shown to the user yet), and re-validate.
4. Exit code 3 (`LayoutError`) means overflow: cut or shorten the least relevant bullet.

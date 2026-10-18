---
name: technical-round
description: Question themes and the round section for a technical interview (ML, data science, GenAI, and agent focus by default), with topic refreshers with plain-language explanations, system design prompts, and resume project deep-dives. Load at I0_intake when the round is technical.
---

# Technical Round

## Themes for the question bank

Pick from the JD's must-haves: ML fundamentals, statistics and experiments, LLMs and RAG, agents and tool use, evaluation, MLOps and deployment, data engineering and SQL, coding. Ask about trade-offs as well as definitions.

## Round section: `## Technical essentials`

### Core topics (5 to 8, ranked by JD weight, with GAP and ASK items first)

For each topic:

```markdown
### Topic: <name>
- **What it is:** 2 sentences, precise.
- **Explain it simply:** analogy, small example, where the analogy breaks (skill `explain-simply`)
- **Trade-offs to mention:** 2 or 3
- **Likely question:** one, with a pointer to the Q number if it's in the bank
```

Use a level 3 heading that does not start with `Q`, so the drill's grep skips topics.

### System design prompts (1 or 2)

An LLM or agent system that fits this team (for example "Design a RAG assistant for internal policy documents"). Skeleton answer: clarifying questions, components and data flow, model and retrieval choices, evaluation plan, cost and latency, failure modes and guardrails, monitoring. Then one sentence explaining it to a non-technical stakeholder.

### Project deep-dives (2 resume projects most relevant to the JD)

Architecture, key decisions and why, metrics (from sources only), what went wrong, and what the candidate would change. Missing details become placeholders. Close each with the plain-language version from `explain-simply`.

### Coding or SQL

If the JD or reported questions mention them, list the practice areas (for example window functions, joins, pandas groupby) and fold them into the study plan.

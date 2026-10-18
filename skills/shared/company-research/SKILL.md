---
name: company-research
description: Search recipe for researching a target company and writing company_brief.md. Load at S0 (intake) of resume tailoring, and whenever you need cited company context for a cover letter, interview prep, or outreach.
---

# Company Research

## Searches (2 to 4 total at intake)

Use `internet_search`. Pick the queries that fit the JD:

1. `"<Company>" what does it do business segments` (topic general)
2. `"<Company>" news` with `topic="news"`, `time_range="year"`: funding, earnings, launches, layoffs, AI initiatives, regulation.
3. `"<Company>" <team or product named in the JD>`, if one is named.
4. `"<Company>" engineering blog OR tech stack machine learning`: stack signals (cloud, data platform, LLM vendors).

Use `web_extract` only on one or two results worth reading in full.

## Source trust

- Best: the company's own site, press releases, investor relations, engineering blog, SEC filings.
- Good: Reuters, Bloomberg, WSJ, FT, TechCrunch, the trade press for that industry.
- Use with care: Glassdoor, Blind, Reddit (opinions; label them).
- Skip: SEO content farms, undated listicles, AI-generated summaries.

Prefer items from the last 12 months. Always write the date.

## company_brief.md

```markdown
# <Company>: brief for <Role>
Researched: <YYYY-MM-DD>

## What they do
2 to 3 sentences. Segments, customers, size if known. [source](url)

## Recent news (last 12 months)
- <YYYY-MM> <one line> [source](url)
(3 to 5 items)

## Team / product
What the JD's team likely works on, from the JD and any public info. Mark guesses as guesses.

## Tech stack signals
- <tool or platform> (where it came from: JD / blog / job posts) [source](url)

## Hooks for the candidate
1 to 3 specific points that connect to the candidate's real work. Used later for the cover letter and summary. Facts about the company only; don't claim anything about the candidate here.
```

Every factual line has a source link. If searches fail, write what the JD says, note "web search unavailable", and move on.

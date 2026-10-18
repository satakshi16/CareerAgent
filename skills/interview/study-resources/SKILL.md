---
name: study-resources
description: Pick study topics and find verified learning resources (YouTube videos, blogs, docs, books, hands-on practice) matched to the user's stated study preference. Load at I0_intake for technical and hiring_manager rounds.
---

# Study Resources

## Topics

Up to 5 topics, ranked by JD weight times how much the candidate needs it. `GAP` and `ASK` items from `gap_analysis.md` come first. Skip topics the resume shows deep, recent work in, unless the JD weighs them heavily.

## Preference to format

`study_pref` is the user's own words. Map it:

| Preference | Search | Good sources |
|---|---|---|
| videos, YouTube, visual | `internet_search("<topic> explained", max_results=3, include_domains=["youtube.com"])` | university lectures, StatQuest, 3Blue1Brown, Andrej Karpathy, DeepLearning.AI, official vendor channels |
| text, reading, blogs | `internet_search("<topic> tutorial guide", max_results=3)` | official docs, engineering blogs, well-known practitioner blogs |
| books | `internet_search("best book on <topic>", max_results=3)` | give title and author only when a result confirms the book exists |
| hands-on, practice | `internet_search("<topic> hands-on tutorial notebook", max_results=3)` | official tutorials, Kaggle, GitHub repos with docs |
| podcasts, audio | `internet_search("<topic> podcast episode", max_results=3)` | episodes, not just show home pages |
| (none) | mixed: one video search and one text search per topic | |

With two named preferences, split the searches between them.

## Budget

At most 6 resource searches per prep. One preference: one search per topic (5 topics). Mixed: the top 3 topics, two searches each. Topics past the budget get a search phrase the user can run themselves, with no link.

## Choosing results

- Only use URLs that came back from the search. Never write a URL from memory.
- Skip YouTube Shorts, paywalled pages, SEO listicles, and undated pages on fast-moving topics (LLMs, agents). For those, prefer material from the last 2 years.
- One or two resources per topic, the best first.

## Output in the prep doc (`## Study plan`)

```markdown
Preference used: <videos / text / mixed default>

1. **<Topic>** (why it matters for this role, one line; about <N> min)
   - [video] <title>, <channel> [link](url)
   - [read] <title>, <site> [link](url)
   - Explain it simply: see Topic: <name> in Technical essentials
```

End with "If you only have one hour:" and the order to go through them in.

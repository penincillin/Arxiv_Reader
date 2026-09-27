---
name: arxiv-reading
description: Collect, deduplicate, rank, and summarize daily arXiv papers about world models, video generation, LLMs, and multimodal LLMs, including affiliation, release status, venue-template evidence, representative figures, and an English HTML digest. Use when the user asks to browse or review an arXiv date, identify top papers, compare research quality, or generate a visual paper-reading report.
---

# arXiv Reading

Build an evidence-backed daily research digest rather than ranking papers from titles alone.

## Scope

Unless the user changes the scope, monitor:

`cs.CV`, `cs.CL`, `cs.AI`, `cs.LG`, `cs.MM`, `cs.RO`, `cs.SD`, `cs.IR`, `stat.ML`, `eess.IV`

Treat multimodal LLMs as part of the LLM topic. Exclude papers whose primary category is mathematics or physics, even if they appear through a cross-list. Do not treat a secondary physics tag as disqualifying when the primary category and contribution are clearly in scope.

## Workflow

1. Interpret a requested date as the date shown in the arXiv daily listing, not the API submission timestamp. State this distinction when reporting results.
2. Run `scripts/collect_daily.py YYYY-MM-DD --output papers.json` to collect every monitored listing, fetch abstracts and metadata, and deduplicate by arXiv ID.
3. Review titles and abstracts semantically. Keyword matches are candidates, not final relevance judgments.
4. Assign papers to the topical groups `world-model`, `video-generation`, and `llm`. A paper may belong to multiple groups.
5. For ranking or quality selection, read [references/ranking.md](references/ranking.md).
6. Verify the strongest candidates from primary sources:
   - Read the abstract and enough of the paper to understand its contribution and evidence.
   - Read the PDF author block for affiliations. Never infer affiliation from a model name, repository name, or email username.
   - Check arXiv comments and the PDF for explicit venue status.
   - Inspect the LaTeX source only to identify template signals. A template is not evidence of submission or acceptance.
   - Open project and repository links to confirm that resources actually exist. Distinguish a demo page, promised release, code, data, and model weights.
7. Select the requested number of papers. If a topic has too few direct matches, include adjacent work only when necessary and label it explicitly.
8. For an HTML digest, read [references/html-report.md](references/html-report.md), use `assets/report-template.html`, and generate one card per ranked selection under a `YYYY_MM_DD/` output directory.
9. Extract one meaningful figure per paper with `scripts/extract_paper_figure.py`. Do not substitute a PDF-page screenshot.
10. Validate counts, links, local image paths, HTML structure, filter behavior, and the absence of Chinese text before delivery.

## Required distinctions

- Report both unique-paper counts and per-list appearances when cross-listing matters.
- Keep `accepted/published`, `submitted`, `template suggests`, and `technical report/preprint` separate.
- Prefer the project page as the title link. If no working project page exists, link the paper PDF.
- Keep rankings provisional for newly posted papers; affiliation and venue are supporting evidence, not substitutes for technical quality.
- Generate the HTML report entirely in English.

## Scripts

- `scripts/collect_daily.py`: collect a dated, deduplicated metadata set from the monitored arXiv categories.
- `scripts/extract_paper_figure.py`: select and convert an actual representative figure using the required fallback order.
- `scripts/render_digest.py`: render a curated JSON selection as `YYYY_MM_DD/summary.html` using the supplied template.

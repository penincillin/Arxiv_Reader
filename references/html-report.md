# HTML Digest Contract

Use `../assets/report-template.html` as the base. Store each digest in a date-named directory using the `YYYY_MM_DD` format. The page must be named `summary.html`, with image assets in its sibling `figures/` directory:

```text
YYYY_MM_DD/
|-- summary.html
`-- figures/
```

## Language and layout

- All visible UI text, metadata, summaries, alt text, and captions must be English.
- Preserve this order inside every paper card: title, affiliation/venue metadata, one-paragraph summary, one figure, then links.
- Group cards by topical category and show their rank within that category.
- If a paper is ranked in multiple categories, repeating its card is acceptable; also report the number of unique papers.
- Include text search plus topic and artifact-release filters.

## Links

- Link the title to a working project page when one exists.
- Otherwise link the title directly to `https://arxiv.org/pdf/ARXIV_ID`.
- A GitHub repository may serve as the project link when it is the paper's only working project resource.
- Verify links before rendering. Do not retain a dead project link.

## Figures

Use this order:

1. Explicitly selected project-page overview or teaser.
2. A meaningful overview, architecture, method, or pipeline figure from arXiv HTML.
3. A real figure extracted from the arXiv source archive or PDF.

Never use a screenshot of the paper page as the figure fallback. Prefer method over result figures when both are informative; otherwise use the clearest central result. Preserve aspect ratio, add descriptive alt text, and identify the figure accurately in the caption.

Run `scripts/extract_paper_figure.py --help` for extraction options. Use `--source-member` when automatic selection misses a source figure or chooses a weak result plot.

## Validation

- Confirm every card has one title link, one metadata line, one summary paragraph, one image, and a caption.
- Confirm the output path is `YYYY_MM_DD/summary.html` and every figure path resolves beneath `YYYY_MM_DD/figures/`.
- Confirm all referenced local images exist and are non-empty.
- Scan for CJK characters to enforce the English-only requirement.
- Check that each topic contains the requested number of ranked cards.
- Clearly mark adjacent papers used to fill a topic quota.

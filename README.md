# arXiv Reading

A Codex skill for discovering, deduplicating, ranking, and summarizing daily arXiv papers about:

- World models
- Video generation
- Large language models
- Multimodal large language models

It can produce an English HTML digest containing ranked papers, affiliations, concise summaries, verified project or PDF links, and one representative figure per paper.

## Install

Clone or copy this directory into a Codex skill location:

```bash
git clone git@github.com:penincillin/Arxiv_Reader.git ~/.agents/skills/arxiv-reading
```

For repository-local use:

```bash
mkdir -p .agents/skills
git clone git@github.com:penincillin/Arxiv_Reader.git .agents/skills/arxiv-reading
```

Codex normally detects new skills automatically. Restart Codex if `$arxiv-reading` does not appear.

## Use

Invoke the skill explicitly:

```text
Use $arxiv-reading to review papers posted on 2026-09-25 and generate a top-10 HTML digest for world models, video generation, and LLMs.
```

The skill may also activate automatically for matching arXiv discovery and review requests.

## Output

Each report uses the following layout:

```text
YYYY_MM_DD/
|-- summary.html
`-- figures/
```

Every paper card follows this order:

```text
Paper title -> Affiliation and venue metadata -> Summary -> Figure -> Links
```

The generated HTML is English-only and includes search plus topic and artifact-release filters.

## Default scope

The default arXiv categories are:

```text
cs.CV, cs.CL, cs.AI, cs.LG, cs.MM,
cs.RO, cs.SD, cs.IR, stat.ML, eess.IV
```

Papers are deduplicated by arXiv ID. Mathematics- and physics-primary papers are excluded by default, even when they appear through cross-listing.

## Ranking signals

Rankings consider:

- Topical relevance
- Technical contribution and experimental evidence
- Availability of code, data, models, or reproducible recipes
- Explicit publication status or weaker venue-template signals
- Team and affiliation context

A conference template is never treated as proof of submission or acceptance.

## Included tools

- `scripts/collect_daily.py` collects a dated arXiv listing and enriches it with API metadata.
- `scripts/extract_paper_figure.py` extracts a real project or paper figure without using paper-page screenshots.
- `scripts/render_digest.py` renders a curated JSON selection with `assets/report-template.html`.

Run any script with `--help` for its command-line options.

## Requirements

- Python 3.10 or newer
- Network access to arXiv and linked project pages
- `pdftoppm` for converting PDF figures to PNG
- `sips` or ImageMagick for non-PNG image conversion when needed

The collection and rendering scripts otherwise use only the Python standard library.

## Notes

- A requested date refers to the date displayed on an arXiv daily listing, which can differ from the API submission timestamp.
- Daily lists can include revised papers as well as new submissions.
- Project links and release status are verified at report-generation time and may change later.
- If a topic lacks enough direct matches, adjacent papers are included only when necessary and labeled explicitly.

## License

No license has been selected yet. Add a license before distributing or accepting external contributions.

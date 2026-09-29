#!/usr/bin/env python3
"""Render a curated arXiv selection JSON as an English HTML digest.

Expected JSON shape:
{
  "title": "arXiv Research Digest",
  "date": "2026-09-25",
  "methodology": "How the papers were selected.",
  "footer": "Optional provenance note.",
  "sections": [{
    "slug": "world-model",
    "name": "World Model",
    "subtitle": "Prediction, planning, and embodied control",
    "papers": [{
      "rank": 1,
      "arxiv_id": "2609.00001",
      "title": "Paper title",
      "affiliation": "Institution or team",
      "venue": "Venue status or template signal",
      "summary": "One paragraph in English.",
      "figure": "figures/2609.00001.png",
      "figure_alt": "Accessible description",
      "figure_caption": "Figure 1: Description.",
      "release": "full",
      "release_label": "Code + model",
      "project_url": "https://example.org/project"
    }]
  }]
}
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path, PurePosixPath


CJK = re.compile(r"[\u3400-\u9fff]")
VALID_RELEASES = {"full", "partial", "none"}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def resolve_figure(output_directory: Path, value: object) -> Path:
    relative = PurePosixPath(str(value))
    if (
        relative.is_absolute()
        or len(relative.parts) < 2
        or relative.parts[0] != "figures"
        or ".." in relative.parts
    ):
        raise ValueError(f"figure path must be beneath figures/: {value}")
    figures_directory = (output_directory / "figures").resolve()
    figure = (output_directory / Path(*relative.parts)).resolve()
    if figure.parent != figures_directory and figures_directory not in figure.parents:
        raise ValueError(f"figure path escapes figures/: {value}")
    return figure


def paper_card(topic: str, paper: dict) -> str:
    required = ["rank", "arxiv_id", "title", "affiliation", "venue", "summary", "figure", "figure_alt", "figure_caption"]
    missing = [key for key in required if not paper.get(key)]
    if missing:
        raise ValueError(f"{paper.get('arxiv_id', 'paper')} is missing: {', '.join(missing)}")
    release = paper.get("release", "none")
    if release not in VALID_RELEASES:
        raise ValueError(f"invalid release value for {paper['arxiv_id']}: {release}")
    pdf_url = paper.get("pdf_url") or f"https://arxiv.org/pdf/{paper['arxiv_id']}"
    primary_url = paper.get("project_url") or pdf_url
    release_label = paper.get("release_label") or {
        "full": "Open artifacts",
        "partial": "Partial release",
        "none": "No artifact found",
    }[release]
    adjacent = '<span class="tag partial">Adjacent work</span>' if paper.get("adjacent") else ""
    project_link = (
        f'<a href="{esc(paper["project_url"])}" target="_blank" rel="noopener noreferrer">Project page</a>'
        if paper.get("project_url") else ""
    )
    return f'''  <article class="paper-card" data-topic="{esc(topic)}" data-release="{esc(release)}">
    <div class="card-head"><div class="title-wrap"><span class="rank">{esc(paper['rank'])}</span><h2><a href="{esc(primary_url)}" target="_blank" rel="noopener noreferrer">{esc(paper['title'])}</a></h2></div><div class="tag-stack"><span class="tag {esc(topic)}">{esc(paper.get('topic_label', topic.replace('-', ' ').title()))}</span>{adjacent}<span class="tag {esc(release)}">{esc(release_label)}</span></div></div>
    <p class="paper-meta">{esc(paper['affiliation'])} · {esc(paper['venue'])} · arXiv:{esc(paper['arxiv_id'])}</p>
    <p class="paper-summary">{esc(paper['summary'])}</p>
    <figure class="paper-figure"><img loading="lazy" src="{esc(paper['figure'])}" alt="{esc(paper['figure_alt'])}"><figcaption>{esc(paper['figure_caption'])}</figcaption></figure>
    <p class="paper-link">{project_link}<a href="{esc(pdf_url)}" target="_blank" rel="noopener noreferrer">PDF</a></p>
  </article>'''


def render(payload: dict, template: str) -> str:
    sections = payload.get("sections", [])
    if not sections:
        raise ValueError("sections must contain at least one topic")
    rendered_sections = []
    all_ids = []
    selection_count = 0
    options = []
    for section in sections:
        slug = section["slug"]
        name = section["name"]
        options.append(f'<option value="{esc(slug)}">{esc(name)}</option>')
        cards = [paper_card(slug, paper) for paper in section.get("papers", [])]
        selection_count += len(cards)
        all_ids.extend(paper["arxiv_id"] for paper in section.get("papers", []))
        rendered_sections.append(
            f'''<section class="category-block" data-topic-block="{esc(slug)}">
  <div class="category-head"><h2>{esc(name)} · Top {len(cards)}</h2><span class="meta">{esc(section.get('subtitle', ''))}</span></div>
{chr(10).join(cards)}
</section>'''
        )
    replacements = {
        "{{REPORT_TITLE}}": esc(payload.get("title", "arXiv Research Digest")),
        "{{REPORT_SUBTITLE}}": esc(payload.get("subtitle", payload.get("date", ""))),
        "{{SELECTION_COUNT}}": str(selection_count),
        "{{UNIQUE_COUNT}}": str(len(set(all_ids))),
        "{{TOPIC_COUNT}}": str(len(sections)),
        "{{METHODOLOGY}}": esc(payload.get("methodology", "Ranked by relevance, technical evidence, release status, venue signals, and team context.")),
        "{{TOPIC_OPTIONS}}": "".join(options),
        "{{PAPER_SECTIONS}}": "\n".join(rendered_sections),
        "{{FOOTER}}": esc(payload.get("footer", "Paper and artifact status reflect information available when this report was generated.")),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if leftovers:
        raise ValueError(f"unresolved template markers: {', '.join(sorted(set(leftovers)))}")
    if CJK.search(template):
        raise ValueError("English-only report requirement violated: CJK text detected")
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection", type=Path, help="Curated selection JSON")
    parser.add_argument("output", type=Path, help="Output path; use YYYY_MM_DD/summary.html")
    parser.add_argument(
        "--template",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "assets" / "report-template.html",
    )
    args = parser.parse_args()
    if args.output.name != "summary.html" or not re.fullmatch(r"\d{4}_\d{2}_\d{2}", args.output.parent.name):
        raise ValueError("output must use the path YYYY_MM_DD/summary.html")
    payload = json.loads(args.selection.read_text())
    for section in payload.get("sections", []):
        for paper in section.get("papers", []):
            figure = resolve_figure(args.output.parent, paper.get("figure", ""))
            if not figure.is_file() or figure.stat().st_size == 0:
                raise ValueError(f"missing or empty figure for {paper.get('arxiv_id', 'paper')}: {figure}")
    document = render(payload, args.template.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(document)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

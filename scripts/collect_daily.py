#!/usr/bin/env python3
"""Collect and deduplicate papers shown on an arXiv daily listing date."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_CATEGORIES = [
    "cs.CV", "cs.CL", "cs.AI", "cs.LG", "cs.MM",
    "cs.RO", "cs.SD", "cs.IR", "stat.ML", "eess.IV",
]
USER_AGENT = "arxiv-reading-skill/1.0"
ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
TOPIC_PATTERNS = {
    "world-model": [
        r"world model", r"world-action model", r"latent dynamics",
        r"predictive embodied", r"action-conditioned predictive", r"object permanence",
    ],
    "video-generation": [
        r"video generation", r"generative video", r"text-to-video", r"image-to-video",
        r"video diffusion", r"audio-video generation", r"video generator",
    ],
    "llm": [
        r"large language model", r"\bllms?\b", r"language model",
        r"vision-language", r"vision language", r"\bvlms?\b", r"\bmllms?\b",
        r"audio-language", r"multimodal", r"multi-modal", r"cross-modal",
    ],
}
EXCLUDED_PRIMARY_PREFIXES = (
    "math.", "physics.", "astro-ph", "cond-mat", "gr-qc", "hep-", "nucl-", "quant-ph",
)


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def strip_markup(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def listing_label(day: dt.date) -> str:
    return f"{day:%a}, {day.day} {day:%b %Y}"


def parse_listing(page: str, label: str) -> list[tuple[str, str]]:
    match = re.search(
        rf"<h3>\s*{re.escape(label)}.*?</h3>(.*?)(?=<h3>|</dl>)",
        page,
        re.DOTALL,
    )
    if not match:
        return []
    papers: list[tuple[str, str]] = []
    for term, definition in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", match.group(1), re.DOTALL):
        id_match = re.search(r'href\s*=\s*"/abs/([^"]+)"', term)
        title_match = re.search(
            r"<div class='list-title mathjax'>.*?<span[^>]*>Title:</span>(.*?)</div>",
            definition,
            re.DOTALL,
        )
        if id_match and title_match:
            papers.append((id_match.group(1), strip_markup(title_match.group(1))))
    return papers


def collect_listings(day: dt.date, categories: list[str]) -> dict[str, dict]:
    label = listing_label(day)
    papers: dict[str, dict] = {}
    for category in categories:
        found: list[tuple[str, str]] = []
        routes = ["pastweek", day.strftime("%Y-%m")]
        for route in routes:
            for skip in range(0, 10000, 2000):
                url = f"https://arxiv.org/list/{category}/{route}?skip={skip}&show=2000"
                try:
                    page = fetch(url).decode("utf-8", "replace")
                except Exception:
                    break
                batch = parse_listing(page, label)
                if batch:
                    found = batch
                    break
                if route == "pastweek" or "No submissions" in page or skip >= 8000:
                    break
            if found:
                break
        for arxiv_id, title in found:
            paper = papers.setdefault(
                arxiv_id,
                {"arxiv_id": arxiv_id, "title": title, "listed_categories": []},
            )
            paper["listed_categories"].append(category)
    return papers


def enrich(papers: dict[str, dict]) -> None:
    ids = list(papers)
    for start in range(0, len(ids), 100):
        chunk = ids[start:start + 100]
        query = urllib.parse.urlencode({"id_list": ",".join(chunk), "max_results": len(chunk)})
        root = ET.fromstring(fetch("https://export.arxiv.org/api/query?" + query))
        for entry in root.findall("a:entry", ATOM):
            arxiv_id = entry.findtext("a:id", "", ATOM).rsplit("/", 1)[-1].split("v")[0]
            if arxiv_id not in papers:
                continue
            paper = papers[arxiv_id]
            primary = entry.find("x:primary_category", ATOM)
            paper.update(
                abstract=" ".join(entry.findtext("a:summary", "", ATOM).split()),
                authors=[author.findtext("a:name", "", ATOM) for author in entry.findall("a:author", ATOM)],
                categories=[node.get("term") for node in entry.findall("a:category", ATOM)],
                comment=" ".join((entry.findtext("x:comment", "", ATOM) or "").split()),
                primary_category=primary.get("term") if primary is not None else "",
                published=entry.findtext("a:published", "", ATOM),
                updated=entry.findtext("a:updated", "", ATOM),
                pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
            )
        if start + 100 < len(ids):
            time.sleep(3.1)


def annotate_topics(paper: dict) -> None:
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    paper["topic_signals"] = [
        topic for topic, patterns in TOPIC_PATTERNS.items()
        if any(re.search(pattern, text) for pattern in patterns)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date", type=dt.date.fromisoformat, help="arXiv listing date in YYYY-MM-DD format")
    parser.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-excluded-primary", action="store_true")
    args = parser.parse_args()

    papers = collect_listings(args.date, args.categories)
    if not papers:
        raise SystemExit(f"No entries found for the arXiv listing date {args.date}")
    enrich(papers)
    records = []
    for paper in papers.values():
        annotate_topics(paper)
        primary = paper.get("primary_category", "")
        if not args.include_excluded_primary and primary.startswith(EXCLUDED_PRIMARY_PREFIXES):
            continue
        records.append(paper)
    records.sort(key=lambda paper: paper["arxiv_id"], reverse=True)
    payload = {
        "listing_date": args.date.isoformat(),
        "monitored_categories": args.categories,
        "unique_papers": len(records),
        "papers": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"wrote {len(records)} unique papers to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

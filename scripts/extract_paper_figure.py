#!/usr/bin/env python3
"""Extract a representative paper figure without using a page screenshot.

Priority:
1. An explicit --figure-url override.
2. A meaningful hero/overview image from --project-url.
3. The best-scoring figure exposed by arXiv HTML.
4. A real figure file extracted from the arXiv source archive.

The command fails when it cannot find a paper figure. It deliberately does not
render the first PDF page as a fallback.
"""

from __future__ import annotations

import argparse
import html
import io
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath


USER_AGENT = "arxiv-digest-figure-extractor/1.0"
POSITIVE = re.compile(
    r"overview|framework|pipeline|method|architecture|teaser|motivation|approach",
    re.IGNORECASE,
)
NEGATIVE = re.compile(r"ablation|appendix|additional|failure case", re.IGNORECASE)


def fetch(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.headers.get_content_type()


def visible_text(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def html_candidates(page_url: str, project_page: bool = False) -> list[tuple[int, str, str]]:
    raw, _ = fetch(page_url)
    page = raw.decode("utf-8", "replace")
    candidates: list[tuple[int, str, str]] = []

    if project_page:
        for match in re.finditer(
            r'<meta[^>]+(?:property|name)=["\'](?:og:image|twitter:image)["\'][^>]+content=["\']([^"\']+)',
            page,
            re.IGNORECASE,
        ):
            candidates.append((90, urllib.parse.urljoin(page_url, html.unescape(match.group(1))), "Project-page hero image"))

    for index, block in enumerate(re.findall(r"<figure\b[^>]*>(.*?)</figure>", page, re.IGNORECASE | re.DOTALL)):
        image_match = re.search(r'<img\b[^>]*src=["\']([^"\']+)', block, re.IGNORECASE)
        if not image_match:
            continue
        caption_match = re.search(r"<figcaption\b[^>]*>(.*?)</figcaption>", block, re.IGNORECASE | re.DOTALL)
        caption = visible_text(caption_match.group(1)) if caption_match else ""
        score = 40 - index
        if index == 0:
            score += 20
        if POSITIVE.search(caption):
            score += 35
        if NEGATIVE.search(caption):
            score -= 20
        image_url = urllib.parse.urljoin(page_url, html.unescape(image_match.group(1)))
        candidates.append((score, image_url, caption or "Representative figure"))

    if project_page and not candidates:
        for index, match in enumerate(re.finditer(r'<img\b[^>]*src=["\']([^"\']+)["\'][^>]*>', page, re.IGNORECASE)):
            tag = match.group(0)
            if re.search(r"logo|icon|avatar|author", tag, re.IGNORECASE):
                continue
            candidates.append((20 - index, urllib.parse.urljoin(page_url, html.unescape(match.group(1))), "Project-page figure"))
    return candidates


def source_candidates(arxiv_id: str) -> tuple[bytes, list[tuple[int, str, str]]]:
    archive, _ = fetch(f"https://export.arxiv.org/e-print/{arxiv_id}")
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as bundle:
        members = {member.name: member for member in bundle.getmembers() if member.isfile()}
        candidates: list[tuple[int, str, str]] = []
        figure_index = 0
        for member in members.values():
            if not member.name.lower().endswith(".tex") or member.size > 2_000_000:
                continue
            source_file = bundle.extractfile(member)
            if source_file is None:
                continue
            source = source_file.read().decode("utf-8", "replace")
            for block in re.findall(r"\\begin\{figure\*?\}(.*?)\\end\{figure\*?\}", source, re.DOTALL):
                figure_index += 1
                graphics = re.findall(r"\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}", block)
                if not graphics:
                    continue
                caption_match = re.search(r"\\caption\{(.*?)\}", block, re.DOTALL)
                caption = " ".join((caption_match.group(1) if caption_match else "").split())
                score = 30 - figure_index
                if figure_index == 1:
                    score += 20
                if POSITIVE.search(caption):
                    score += 35
                if NEGATIVE.search(caption):
                    score -= 20
                base = PurePosixPath(member.name).parent
                raw_names = [str(base / graphics[0]), graphics[0]]
                names: list[str] = []
                for raw_name in raw_names:
                    if PurePosixPath(raw_name).suffix:
                        names.append(raw_name)
                    else:
                        names.extend(raw_name + ext for ext in (".pdf", ".png", ".jpg", ".jpeg"))
                selected = next((name for name in names if name in members), None)
                if selected:
                    candidates.append((score, selected, caption or "Representative figure"))
        return archive, candidates


def convert_to_png(data: bytes, content_type: str, output: Path) -> None:
    if data.startswith(b"\x89PNG"):
        output.write_bytes(data)
        return
    with tempfile.TemporaryDirectory(prefix="arxiv-figure-") as directory:
        source = Path(directory) / "source"
        source.write_bytes(data)
        if data.startswith(b"%PDF"):
            subprocess.run(
                ["pdftoppm", "-f", "1", "-l", "1", "-png", "-scale-to-x", "1600", "-scale-to-y", "-1", "-singlefile", str(source), str(output.with_suffix(""))],
                check=True,
            )
            return
        converter = shutil.which("sips") or shutil.which("magick")
        if not converter:
            raise RuntimeError(f"Cannot convert {content_type or 'unknown image type'} to PNG")
        if Path(converter).name == "sips":
            subprocess.run([converter, "-s", "format", "png", str(source), "--out", str(output)], check=True, stdout=subprocess.DEVNULL)
        else:
            subprocess.run([converter, str(source), str(output)], check=True)


def extract_source_member(archive: bytes, member_name: str) -> tuple[bytes, str]:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:*") as bundle:
        member = bundle.getmember(member_name)
        source = bundle.extractfile(member)
        if source is None:
            raise RuntimeError(f"Unable to extract {member_name}")
        suffix = PurePosixPath(member_name).suffix.lower()
        content_type = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(suffix, "application/octet-stream")
        return source.read(), content_type


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arxiv_id")
    parser.add_argument("output", type=Path, help="Output PNG path")
    parser.add_argument("--project-url")
    parser.add_argument("--figure-url", help="Explicit representative image override")
    parser.add_argument("--source-member", help="Explicit path inside the arXiv source archive")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.figure_url:
        data, content_type = fetch(args.figure_url)
        convert_to_png(data, content_type, args.output)
        print(f"explicit figure: {args.figure_url}")
        return 0

    if args.project_url:
        try:
            candidates = html_candidates(args.project_url, project_page=True)
        except Exception as error:
            print(f"project-page lookup failed: {error}", file=sys.stderr)
            candidates = []
        if candidates:
            _, url, caption = max(candidates)
            data, content_type = fetch(url)
            convert_to_png(data, content_type, args.output)
            print(f"project figure: {url}\ncaption: {caption}")
            return 0

    try:
        candidates = html_candidates(f"https://arxiv.org/html/{args.arxiv_id}")
    except Exception as error:
        print(f"arXiv HTML lookup failed: {error}", file=sys.stderr)
        candidates = []
    if candidates:
        _, url, caption = max(candidates)
        data, content_type = fetch(url)
        convert_to_png(data, content_type, args.output)
        print(f"arXiv HTML figure: {url}\ncaption: {caption}")
        return 0

    archive, candidates = source_candidates(args.arxiv_id)
    if args.source_member:
        selected = args.source_member
        caption = "Explicit source-member override"
    elif candidates:
        _, selected, caption = max(candidates)
    else:
        raise RuntimeError("No paper figure found; refusing to use a page screenshot")
    data, content_type = extract_source_member(archive, selected)
    convert_to_png(data, content_type, args.output)
    print(f"arXiv source figure: {selected}\ncaption: {caption}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)

# -*- coding: utf-8 -*-
"""
Regenerates sitemap.xml from the actual pages in the repo, so it can't drift
from what's really published. Excludes 404.html, templates/, and anything
with <meta name="robots" content="noindex">.

Usage:
    python scripts/build_sitemap.py
"""
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://www.aidata.works"

EXCLUDE_NAMES = {"404.html"}


def is_noindex(text):
    return bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', text, re.IGNORECASE))


def target_pages():
    pages = [p for p in ROOT.glob("*.html") if p.name not in EXCLUDE_NAMES]
    pages += list(ROOT.glob("case-studies/*/index.html"))
    return sorted(pages)


def url_for(page):
    rel = page.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return BASE_URL + "/"
    if rel.endswith("/index.html"):
        return BASE_URL + "/" + rel[: -len("index.html")]
    return BASE_URL + "/" + rel


def priority_for(url):
    if url == BASE_URL + "/":
        return "1.0"
    if "/case-studies/" in url and url != BASE_URL + "/case-studies.html":
        return "0.7"
    return "0.8"


def main():
    today = date.today().isoformat()
    entries = []
    for page in target_pages():
        text = page.read_text(encoding="utf-8")
        if is_noindex(text):
            continue
        url = url_for(page)
        entries.append((url, priority_for(url)))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{today}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")

    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote sitemap.xml with {len(entries)} URLs")


if __name__ == "__main__":
    main()

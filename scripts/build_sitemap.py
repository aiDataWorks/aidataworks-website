# -*- coding: utf-8 -*-
"""
Regenerates sitemap.xml from the actual pages in the repo, so it can't drift
from what's really published. Excludes 404.html, templates/, and anything
with <meta name="robots" content="noindex">. Each page's <lastmod> is the
date of its last git commit.

Usage:
    python scripts/build_sitemap.py
"""
import re
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://www.aidata.works"

EXCLUDE_NAMES = {"404.html"}


def is_noindex(text):
    return bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', text, re.IGNORECASE))


def target_pages():
    pages = [p for p in ROOT.glob("*.html") if p.name not in EXCLUDE_NAMES]
    # Every <section>/<slug>/index.html: case-studies, blog, whitepapers,
    # events, news - and any section added later.
    pages += list(ROOT.glob("*/*/index.html"))
    return sorted(pages)


def url_for(page):
    rel = page.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return BASE_URL + "/"
    if rel.endswith("/index.html"):
        return BASE_URL + "/" + rel[: -len("index.html")]
    return BASE_URL + "/" + rel


def lastmod_for(page):
    # Date of the last commit that touched the page, so the sitemap only
    # changes when a page does. Falls back to today for uncommitted pages.
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(page)],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return out or date.today().isoformat()


def priority_for(url):
    if url == BASE_URL + "/":
        return "1.0"
    if url.endswith("/"):  # a <section>/<slug>/ detail page
        return "0.7"
    return "0.8"


def main():
    entries = []
    for page in target_pages():
        text = page.read_text(encoding="utf-8")
        if is_noindex(text):
            continue
        url = url_for(page)
        entries.append((url, priority_for(url), lastmod_for(page)))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority, lastmod in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    lines.append("")

    (ROOT / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote sitemap.xml with {len(entries)} URLs")


if __name__ == "__main__":
    main()

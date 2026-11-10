# -*- coding: utf-8 -*-
"""
Catches the mistakes that would put a broken page on the live site.
Run by .github/workflows/site.yml after build_nav.py, and fails the build
(so nothing broken gets committed) if any ERROR is found.

ERRORS (block the build):
  - a page has no site header or footer (its <header>/<footer> tags were
    deleted, so build_nav.py had nothing to fill in)
  - a page doesn't load site.js (without it the nav menus don't open)
  - a page sits in a folder that isn't a known section (e.g. "blogs/" for "blog/")
  - a blog post, whitepaper, event or news item:
      still contains [PLACEHOLDER] text from its template
      is missing its <title>, meta description, canonical link or <h1>
      has a canonical link that doesn't match its folder
      isn't linked from its listing page (blog.html, whitepapers.html, ...)
  - the case-studies.html data block isn't valid JSON, or points at a missing page
  - those pages, their listing pages, or faq.html link to a page, image or
    file that doesn't exist

WARNINGS (reported, don't block):
  - broken links on other pages, including case studies (several existed
    before these checks did)

Usage:
    python scripts/check_site.py
"""
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
IN_CI = os.environ.get("GITHUB_ACTIONS") == "true"

# folder -> (listing page, template, strict link checking)
SECTIONS = {
    "blog":         ("blog.html",         "blog-post-template.html",  True),
    "whitepapers":  ("whitepapers.html",  "whitepaper-template.html", True),
    "events":       ("webinars.html",     "event-template.html",      True),
    "news":         ("newsroom.html",     "news-template.html",       True),
    "case-studies": ("case-studies.html", None,                       False),
}
STRICT_ROOT_PAGES = {"faq.html"} | {listing for listing, _, strict in SECTIONS.values() if strict}

errors, warnings = [], []


def report(bucket, page, message):
    bucket.append((page.relative_to(ROOT).as_posix(), message))


def site_pages():
    return sorted(list(ROOT.glob("*.html")) + list(ROOT.glob("*/*/index.html")))


def strip_comments_and_inline_scripts(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return re.sub(r"<script\b(?![^>]*\bsrc=)[^>]*>.*?</script>", "", text, flags=re.DOTALL)


def local_refs(page, text):
    for m in re.finditer(r'(?:href|src)="([^"]+)"', strip_comments_and_inline_scripts(text)):
        url = m.group(1)
        if re.match(r"(https?:|mailto:|tel:|#|data:|javascript:)", url):
            continue
        path = unquote(url.split("#")[0].split("?")[0])
        if path:
            yield url, path


def resolves(page, path):
    target = (ROOT / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
    if path.endswith("/"):
        target = target / "index.html"
    return target.exists()


def template_placeholders(template):
    if not template:
        return set()
    text = (ROOT / "templates" / template).read_text(encoding="utf-8")
    return set(re.findall(r"\[[^\[\]<>\n]+\]", text))


def is_strict(page):
    rel = page.relative_to(ROOT)
    if len(rel.parts) == 1:
        return rel.name in STRICT_ROOT_PAGES
    return SECTIONS.get(rel.parts[0], (None, None, True))[2]


def check_detail_page(page, section, placeholders):
    visible = re.sub(r"<!--.*?-->", "", page.read_text(encoding="utf-8"), flags=re.DOTALL)
    left = sorted(p for p in placeholders if p in visible)
    if left:
        report(errors, page, "still has template placeholder text: " + ", ".join(left[:5])
               + (" ..." if len(left) > 5 else ""))
    if not re.search(r"<title>[^<\s][^<]*</title>", visible):
        report(errors, page, "is missing a <title>.")
    if not re.search(r'<meta name="description" content="[^"\s][^"]*">', visible):
        report(errors, page, "is missing its meta description.")
    if not re.search(r"<h1\b[^>]*>\s*[^<\s]", visible):
        report(errors, page, "is missing its <h1> headline.")
    canonical = re.search(r'<link rel="canonical" href="([^"]*)">', visible)
    expected = f"https://www.aidata.works/{section}/{page.parent.name}/"
    if not canonical or canonical.group(1) != expected:
        report(errors, page, f'canonical link should be "{expected}" (it must match the folder name).')


def main():
    for page in site_pages():
        text = page.read_text(encoding="utf-8")

        # Look outside comments, so a header swallowed by an unclosed comment still counts as missing.
        uncommented = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        if 'class="nav-inner"' not in uncommented:
            report(errors, page, "has no site header. Make sure the page still contains "
                                 '<header class="nav" id="nav"></header> right after <body>.')
        if 'class="footer-inner' not in uncommented:
            report(errors, page, "has no site footer. Make sure the page still contains "
                                 '<footer class="site-footer"></footer> before the closing </body>.')

        if not re.search(r'<script src="(?:\.\./)*site\.js"></script>', uncommented):
            report(errors, page, 'doesn\'t load site.js, so its menus won\'t open. Add <script src="site.js"></script> '
                                 '(or "../../site.js" in a section folder) before </body>.')

        for url, path in local_refs(page, text):
            if not resolves(page, path):
                report(errors if is_strict(page) else warnings, page, f'links to "{url}", which does not exist.')

    for folder in sorted({p.relative_to(ROOT).parts[0] for p in ROOT.glob("*/*/index.html")} - set(SECTIONS)):
        report(errors, ROOT / folder, "is not a known section folder. Content goes in one of: "
               + ", ".join(f"{s}/" for s in SECTIONS) + ".")

    for section, (listing, template, _) in SECTIONS.items():
        placeholders = template_placeholders(template)
        pages = sorted(ROOT.glob(f"{section}/*/index.html"))
        for page in pages:
            check_detail_page(page, section, placeholders)
        # Listings may link to items from a <script> data block (case-studies.html), so keep scripts here.
        listing_text = re.sub(r"<!--.*?-->", "", (ROOT / listing).read_text(encoding="utf-8"), flags=re.DOTALL)
        linked = set(re.findall(r'%s/([^/"]+)/' % re.escape(section), listing_text))
        for page in pages:
            if page.parent.name not in linked:
                report(errors, page, f"is not linked from {listing}. Add a card for it there.")

    # case-studies.html builds its cards from a JSON block; one typo blanks the page.
    cs_listing = ROOT / "case-studies.html"
    m = re.search(r'<script type="application/json" id="case-studies-data">(.*?)</script>',
                  cs_listing.read_text(encoding="utf-8"), re.DOTALL)
    try:
        entries = json.loads(m.group(1)) if m else []
        for entry in entries:
            url = entry.get("detailUrl") or ""
            if url and not (ROOT / url).exists():
                report(errors, cs_listing, f'case study "{entry.get("slug")}" has detailUrl "{url}", which does not exist.')
    except json.JSONDecodeError as e:
        report(errors, cs_listing, f"case-studies-data is not valid JSON (line {e.lineno} of the block: {e.msg}). "
                                   "Check for a missing comma or quote. The listing page shows no cards until this is fixed.")

    for kind, items in (("warning", warnings), ("error", errors)):
        for page, message in items:
            if IN_CI:
                print(f"::{kind} file={page}::{page} {message}")
            else:
                print(f"{kind.upper()}: {page} {message}")

    print(f"\nChecked {len(site_pages())} pages: {len(errors)} error(s), {len(warnings)} warning(s).")
    if errors:
        print("Fix the errors above and push again.")
        sys.exit(1)


if __name__ == "__main__":
    main()

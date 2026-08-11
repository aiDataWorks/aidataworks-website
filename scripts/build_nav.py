# -*- coding: utf-8 -*-
"""
Keeps the header and footer identical across every page.

partials/header.html and partials/footer.html are the single source of
truth. Edit those, then run this script - it stamps the rendered header/
footer into every page's <header>...</header> and <footer>...</footer>,
adjusting relative paths (assets/, styles.css, other pages) automatically
for how deep the page sits (root vs case-studies/<slug>/index.html).

index.html is the one page that intentionally differs: it gets the larger
nav-logo--lg / footer-logo--lg logo variants. Nothing else about the header
or footer is allowed to vary page-to-page - if it needs to, that's a partial
change, not a per-page edit.

Usage:
    python scripts/build_nav.py            # rewrite all pages
    python scripts/build_nav.py --check    # report drift, change nothing
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "partials"

REL_ATTR_RE = re.compile(r'(href|src)="(?!https?://|#|mailto:|tel:)([^"]*)"')


def render(partial_text, root_prefix, is_landing):
    text = REL_ATTR_RE.sub(lambda m: f'{m.group(1)}="{root_prefix}{m.group(2)}"', partial_text)
    if is_landing:
        # Nav logo stays the standard size on the landing page too (matches
        # every other page, per explicit request). Only the footer logo is
        # larger on the landing page.
        text = text.replace('class="footer-logo"', 'class="footer-logo footer-logo--lg"')
    return text


def target_pages():
    pages = [p for p in ROOT.glob("*.html")]
    pages += list(ROOT.glob("case-studies/*/index.html"))
    return sorted(pages)


def root_prefix_for(page_path):
    rel = page_path.relative_to(ROOT)
    depth = len(rel.parts) - 1  # case-studies/<slug>/index.html -> depth 2
    return "../" * depth


def main():
    check_only = "--check" in sys.argv

    header_partial = (PARTIALS / "header.html").read_text(encoding="utf-8")
    footer_partial = (PARTIALS / "footer.html").read_text(encoding="utf-8")

    changed, unchanged, skipped = [], [], []

    for page in target_pages():
        text = page.read_text(encoding="utf-8")
        if "<header" not in text or "<footer" not in text:
            skipped.append(page)
            continue

        is_landing = page.name == "index.html" and page.parent == ROOT
        prefix = root_prefix_for(page)

        new_header = render(header_partial, prefix, is_landing)
        new_footer = render(footer_partial, prefix, is_landing)

        new_text = re.sub(r"<header.*?</header>", lambda m: new_header, text, count=1, flags=re.DOTALL)
        new_text = re.sub(r"<footer.*?</footer>", lambda m: new_footer, new_text, count=1, flags=re.DOTALL)

        if new_text != text:
            changed.append(page)
            if not check_only:
                page.write_text(new_text, encoding="utf-8")
        else:
            unchanged.append(page)

    verb = "Would update" if check_only else "Updated"
    print(f"{verb} {len(changed)} page(s):")
    for p in changed:
        print(f"  {p.relative_to(ROOT)}")
    print(f"Already in sync: {len(unchanged)} page(s)")
    if skipped:
        print(f"Skipped (no <header>/<footer> found - not a site page): {len(skipped)}")
        for p in skipped:
            print(f"  {p.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

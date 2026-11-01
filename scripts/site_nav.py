#!/usr/bin/env python3
"""Render the shared header and stamp it into every page that already has one.

The markup lives in includes/site-nav.html. Page-specific pieces stay put:
the Calendly CTA (href, UTMs, data-track attributes, label) is copied out of
the existing nav, and aria-current is set from the page URL.

Usage (from the repo root):
    python3 scripts/site_nav.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "includes" / "site-nav.html"
PLACEHOLDER = "__NAV_CTA__"

# Landing pages that intentionally have no site header. Never invent a nav there.
SKIP_PARTS = {
    "15minutepipelineteardown",
    "ai-agents",
}


def file_to_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


def path_matches(href: str, url_path: str) -> bool:
    if href in {"", "/"}:
        return False
    path = url_path.split("?", 1)[0].split("#", 1)[0]
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    if href == "/blog/":
        return path == "/blog/" or path.startswith("/blog/")
    if href == "/about/":
        return path in {"/about/", "/about.html"}
    if href.endswith(".html"):
        return path == href
    return path.rstrip("/") == href.rstrip("/")


def load_template() -> str:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->\s*", "", text, count=1, flags=re.S)
    if PLACEHOLDER not in text:
        raise SystemExit(f"{TEMPLATE_PATH} is missing {PLACEHOLDER}")
    return text.strip()


def mark_current(html: str, url_path: str) -> str:
    def repl_anchor(match: re.Match) -> str:
        tag = match.group(0)
        if "nav-cta" in tag or "nav-logo" in tag:
            return tag
        href_match = re.search(r'href="([^"]*)"', tag)
        if not href_match or "aria-current=" in tag:
            return tag
        if path_matches(href_match.group(1), url_path):
            return tag[:-1] + ' aria-current="page">'
        return tag

    html = re.sub(r"<a\b[^>]*>", repl_anchor, html)
    token_re = re.compile(r"<li\b[^>]*>|</li>")
    opens: list[tuple[int, int, bool]] = []
    insert_at: list[int] = []
    for match in token_re.finditer(html):
        token = match.group(0)
        if token.startswith("</"):
            if not opens:
                continue
            start, open_end, is_dropdown = opens.pop()
            if is_dropdown and 'aria-current="page"' in html[open_end : match.start()]:
                insert_at.append(start)
        else:
            opens.append((match.start(), match.end(), "has-dropdown" in token))
    for start in reversed(insert_at):
        open_match = re.match(r"<li\b[^>]*>", html[start:])
        if not open_match:
            continue
        tag = open_match.group(0)
        if "is-ancestor" in tag:
            continue
        replacement = tag.replace(
            'class="has-dropdown"', 'class="has-dropdown is-ancestor"', 1
        )
        html = html[:start] + replacement + html[start + len(tag) :]
    return html


def render_nav(cta_html: str, url_path: str) -> str:
    if not cta_html or "nav-cta" not in cta_html:
        raise SystemExit("nav CTA is missing; refusing to stamp a header without it")
    html = load_template().replace(PLACEHOLDER, cta_html.strip())
    return mark_current(html, url_path)


def extract_cta(nav_html: str) -> str:
    match = re.search(r'<a\b[^>]*\bclass="nav-cta"[^>]*>.*?</a>', nav_html, flags=re.S)
    if not match:
        raise SystemExit("existing nav has no .nav-cta anchor")
    return match.group(0)


def strip_inline_nav_ready(text: str) -> str:
    """Drop DOMContentLoaded blocks whose only job is the old nav toggle.

    Mixed scroll/reveal scripts are left alone. site-nav.js owns the menu,
    and it stops the click before those older button listeners can double-toggle.
    """
    marker = "document.addEventListener('DOMContentLoaded', function() {"
    pieces: list[str] = []
    cursor = 0
    while True:
        found = text.find(marker, cursor)
        if found == -1:
            pieces.append(text[cursor:])
            break
        start = found
        line_start = text.rfind("\n", 0, found) + 1
        prev_end = line_start - 1
        prev_start = text.rfind("\n", 0, max(prev_end, 0)) + 1
        prev_line = text[prev_start:prev_end]
        if "nav toggle" in prev_line.lower() or "Mobile-aware nav" in prev_line:
            start = prev_start
        brace = text.find("{", found)
        depth = 0
        index = brace
        while index < len(text):
            char = text[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    index += 1
                    break
            index += 1
        tail = re.match(r"\s*\);", text[index:])
        end = index + (tail.end() if tail else 0)
        body = text[found:end]
        nav_only = (
            "navToggle" in body
            and "reveal" not in body
            and "expandAll" not in body
            and "fwForm" not in body
        )
        if nav_only:
            pieces.append(text[cursor:start])
        else:
            pieces.append(text[cursor:end])
        cursor = end
    text = "".join(pieces)
    text = re.sub(r"\n[ \t]*<script>\s*</script>", "", text)
    return text


def ensure_assets(text: str) -> str:
    if "</head>" not in text:
        raise SystemExit("page is missing </head>")
    if "/assets/site-nav.css" not in text:
        text = text.replace(
            "</head>",
            '  <link rel="stylesheet" href="/assets/site-nav.css">\n</head>',
            1,
        )
    if "/assets/site-nav.js" not in text:
        text = text.replace(
            "</head>",
            '  <script src="/assets/site-nav.js" defer></script>\n</head>',
            1,
        )
    return text


def stamp_text(text: str, url_path: str) -> str:
    match = re.search(r"<nav id=\"nav\"[^>]*>.*?</nav>", text, flags=re.S)
    if not match:
        return text
    cta = extract_cta(match.group(0))
    nav = render_nav(cta, url_path)
    text = text[: match.start()] + nav + text[match.end() :]
    text = strip_inline_nav_ready(text)
    text = ensure_assets(text)
    if cta not in text:
        raise SystemExit(f"CTA was not preserved for {url_path}")
    return text


def stamp_file(path: Path) -> bool:
    if path.resolve() == TEMPLATE_PATH.resolve():
        return False
    if any(part in SKIP_PARTS or part == "includes" for part in path.parts):
        return False
    original = path.read_text(encoding="utf-8")
    if '<nav id="nav"' not in original:
        return False
    updated = stamp_text(original, file_to_url(path))
    if updated != original:
        path.write_text(updated, encoding="utf-8")
    return True


def main() -> int:
    pages = sorted(ROOT.rglob("*.html"))
    stamped = 0
    for path in pages:
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        if stamp_file(path):
            stamped += 1
            print(f"stamped {path.relative_to(ROOT)}")
    print(f"stamped {stamped} pages from {TEMPLATE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate static HTML: JSON-LD parses, internal links resolve, blog template holds."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://rncld.com"
SKIP_PREFIXES = ("/cdn-cgi/",)

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def local_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() in {".html", ".xml", ".txt", ".css", ".svg", ".png", ".jpg", ".jpeg", ".webp", ".pdf", ".mp4"}:
            yield path


def resolve(url: str) -> Path | None:
    path = url.split("#", 1)[0].split("?", 1)[0]
    if path.startswith(SITE):
        path = path[len(SITE):] or "/"
    if not path.startswith("/"):
        return None
    if any(path.startswith(prefix) for prefix in SKIP_PREFIXES):
        return None
    rel = path.lstrip("/")
    if rel == "":
        return ROOT / "index.html"
    candidate = ROOT / rel
    if candidate.is_dir() or rel.endswith("/"):
        return candidate / "index.html"
    return candidate


def visible_text(fragment: str) -> str:
    fragment = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    for src, dst in (("\u2019", "'"), ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'), ("\u2014", "-"), ("\u2013", "-"), ("\u00a0", " ")):
        fragment = fragment.replace(src, dst)
    return re.sub(r"\s+", " ", fragment).strip().lower()


def strip_added(chunk: str) -> str:
    patterns = (
        r'<aside class="takeaways".*?</aside>',
        r'<div class="post-video".*?</div>',
        r'<figure class="post-video".*?</figure>',
        r'<div class="post-cta".*?</div>',
        r'<section class="post-faq".*?</section>',
        r'<aside class="post-related".*?</aside>',
        r'<div class="post-nav">.*?</div>',
    )
    for pattern in patterns:
        chunk = re.sub(pattern, " ", chunk, flags=re.S)
    return chunk


def check_links(path: Path, text: str) -> None:
    for match in re.finditer(r'''(?:href|src)\s*=\s*["']([^"']+)["']''', text):
        url = html.unescape(match.group(1)).strip()
        if not url or url.startswith(("mailto:", "http://", "https://", "data:", "tel:", "#", "javascript:")):
            continue
        target = resolve(url if url.startswith("/") else "/" + url)
        if target is None:
            continue
        if not target.is_file():
            fail(f"{path.relative_to(ROOT)}: missing {url} -> {target.relative_to(ROOT)}")


def check_jsonld(path: Path, text: str) -> list[dict]:
    found = []
    for match in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, flags=re.S):
        raw = match.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            fail(f"{path.relative_to(ROOT)}: invalid JSON-LD ({exc})")
            continue
        found.append(data)
    return found


def types_of(data) -> set[str]:
    found = set()
    if isinstance(data, list):
        for item in data:
            found |= types_of(item)
        return found
    if not isinstance(data, dict):
        return found
    kind = data.get("@type")
    if isinstance(kind, str):
        found.add(kind)
    elif isinstance(kind, list):
        found.update(k for k in kind if isinstance(k, str))
    if "@graph" in data:
        found |= types_of(data["@graph"])
    return found


def check_post(path: Path, text: str, blocks: list[dict]) -> None:
    kinds = set()
    for block in blocks:
        kinds |= types_of(block)
    for required in ("BlogPosting", "FAQPage", "BreadcrumbList"):
        if required not in kinds:
            fail(f"{path.name}: missing {required}")
    has_video = 'data-video-slot="ready"' in text
    has_empty = 'data-video-slot="empty"' in text
    if has_video and "VideoObject" not in kinds:
        fail(f"{path.name}: video slot is ready but VideoObject is missing")
    if has_empty and "VideoObject" in kinds:
        fail(f"{path.name}: empty video slot should not emit VideoObject")
    if not has_video and not has_empty:
        fail(f"{path.name}: missing video slot")
    slug = path.stem
    campaign = f"utm_campaign=blog_{slug}"
    if text.count(campaign) < 4:
        fail(f"{path.name}: expected utm_campaign=blog_{slug} on nav, footer, and both CTAs")
    if 'data-cta-block="inbody"' not in text or 'data-cta-block="post_end"' not in text:
        fail(f"{path.name}: missing inbody or post_end CTA")
    if "Key takeaways" not in text:
        fail(f"{path.name}: missing key takeaways")
    source = ROOT / "blog" / "posts" / f"{slug}.md"
    if source.is_file():
        raw = source.read_text(encoding="utf-8")
        meta, _, body = raw.partition("---")
        # partition splits the opening fence; split again
        _, _, rest = raw.split("---", 2)
        if "format: html" in raw.split("---", 2)[1]:
            page_body = re.search(r'<div class="post-body">(.*)</div>\s*<footer', text, flags=re.S)
            if not page_body:
                fail(f"{path.name}: post body not found for wording check")
            else:
                src = visible_text(rest)
                out = visible_text(strip_added(page_body.group(1)))
                if src != out:
                    fail(f"{path.name}: article wording drifted from blog/posts/{slug}.md")


def check_sitemap() -> None:
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", text)
    required = [
        f"{SITE}/blog/outbound-reply-rates-2026.html",
        f"{SITE}/blog/bofu-content-that-moves-deals.html",
        f"{SITE}/blog/why-gtm-builds-fail.html",
        f"{SITE}/problems/first-sales-hire/",
        f"{SITE}/problems/outbound-not-landing/",
        f"{SITE}/problems/founder-led-sales-trap/",
        f"{SITE}/problems/pipeline-not-growing/",
        f"{SITE}/about/",
        f"{SITE}/faq/",
        f"{SITE}/videos/",
    ]
    for loc in required:
        if loc not in locs:
            fail(f"sitemap missing {loc}")
    for loc in locs:
        target = resolve(loc)
        if target is None or not target.is_file():
            fail(f"sitemap loc does not resolve: {loc}")
    claude = (ROOT / "blog" / "claudeforce-for-hubspot.html").read_text(encoding="utf-8")
    ants = "https://www.withants.com/blog/claudeforce-for-hubspot/"
    if f'rel="canonical" href="{ants}"' not in claude and f"rel=\"canonical\" href=\"{ants}\"" not in claude:
        if ants not in claude.split("canonical", 1)[-1][:180]:
            fail("claudeforce canonical does not point at the Ants post")
    if f"{SITE}/blog/claudeforce-for-hubspot.html" in locs:
        fail("claudeforce is canonicalized to Ants and should not be in the sitemap")
    if any("/bofu/" in loc for loc in locs):
        fail("unlisted BoFu keyword pages are on hold and must not be in the sitemap")


def main() -> int:
    html_files = [p for p in local_files() if p.suffix == ".html"]
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        blocks = check_jsonld(path, text)
        check_links(path, text)
        if path.parent == ROOT / "blog" and path.name != "index.html":
            check_post(path, text, blocks)
    check_sitemap()
    if errors:
        print(f"{len(errors)} problem(s):")
        for item in errors:
            print(" -", item)
        return 1
    print(f"ok: {len(html_files)} html files, JSON-LD parses, internal links resolve, sitemap matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())

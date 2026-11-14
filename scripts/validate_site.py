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
    campaign = f"utm_campaign={slug}&amp;"
    if text.count(campaign) < 4:
        fail(f"{path.name}: expected utm_campaign={slug} on nav, footer, and both CTAs")
    if "utm_source=rncld&amp;utm_medium=site" not in text:
        fail(f"{path.name}: Calendly CTAs are missing utm_source=rncld&utm_medium=site")
    if "Book the 20 Minute Teardown" not in text:
        fail(f"{path.name}: missing the 20 Minute Teardown CTA")
    if 'href="/gtm-autopsy/?' in text or "gtm-autopsy/?" in text:
        fail(f"{path.name}: internal /gtm-autopsy/ link has a query string")
    if "/assets/track.js" not in text:
        fail(f"{path.name}: missing /assets/track.js")
    if "data-cta-id=" not in text or "data-cta-position=" not in text:
        fail(f"{path.name}: CTA is missing data-cta-id or data-cta-position")
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
        f"{SITE}/15minutepipelineteardown/",
        f"{SITE}/gtm-autopsy/",
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
    if f"{SITE}/audit.html" in locs:
        fail("audit.html redirects to /gtm-autopsy/ and should not be in the sitemap")
    if f"{SITE}/about.html" in locs:
        fail("about.html duplicates /about/ and should not be in the sitemap")
    if f"{SITE}/outside-audit/" in locs:
        fail("outside-audit redirects to /15minutepipelineteardown/ and should not be in the sitemap")
    for retired in ("/ai-agents.html", "/bofu-content.html", "/content.html", "/demand-generation.html"):
        if f"{SITE}{retired}" in locs:
            fail(f"{retired} is a redirect and should not be in the sitemap")


def check_offer_name(path: Path, text: str) -> None:
    if "GTM Audit" in text:
        fail(f"{path.relative_to(ROOT)}: still says GTM Audit")
    bare = re.sub(r"100-Point GTM Autopsy", "", text)
    if "GTM Autopsy" in bare:
        fail(f"{path.relative_to(ROOT)}: bare GTM Autopsy (use 100-Point GTM Autopsy)")


def check_nav(path: Path, text: str) -> None:
    if '<nav id="nav"' not in text or "includes" in path.parts:
        return
    nav_match = re.search(r'<nav id="nav"[^>]*>.*?</nav>', text, flags=re.S)
    if not nav_match:
        fail(f"{path.relative_to(ROOT)}: nav id is unclosed")
        return
    nav = nav_match.group(0)
    if 'id="navToggle"' not in nav or 'aria-controls="navLinks"' not in nav or 'aria-expanded="false"' not in nav:
        fail(f"{path.relative_to(ROOT)}: hamburger is missing aria-expanded or aria-controls")
    if 'type="button"' not in nav:
        fail(f"{path.relative_to(ROOT)}: nav toggle is not a button")
    if "/assets/site-nav.css" not in text or "/assets/site-nav.js" not in text:
        fail(f"{path.relative_to(ROOT)}: shared nav assets are not linked")
    if 'class="nav-cta"' not in nav:
        fail(f"{path.relative_to(ROOT)}: nav CTA is missing")
    required = [
        "/gtm-autopsy/",
        "/15minutepipelineteardown/",
        "/gtm-consulting.html",
        "/pricing/",
        "/problems/outbound-not-landing/",
        "/problems/pipeline-not-growing/",
        "/problems/first-sales-hire/",
        "/problems/founder-led-sales-trap/",
        "/blog/",
        "/videos/",
        "/faq/",
        "/about/",
    ]
    for href in required:
        if f'href="{href}"' not in nav:
            fail(f"{path.relative_to(ROOT)}: nav is missing {href}")
    for banned in ("/ai-agents", "/bofu-content", "/demand-generation", "/content.html", "/audit.html", "/outside-audit/"):
        if banned in nav:
            fail(f"{path.relative_to(ROOT)}: unlisted page {banned} is in the nav")
    # Five top-level destinations: four groups plus About. The CTA is not one of them.
    groups = len(re.findall(r'<li class="has-dropdown(?: is-ancestor)?">', nav))
    if groups != 4:
        fail(f"{path.relative_to(ROOT)}: expected 4 nav groups, found {groups}")
    if not re.search(r'<li><a\b[^>]*href="/about/"', nav):
        fail(f"{path.relative_to(ROOT)}: About is not a top-level nav item")


def check_tracking(path: Path, text: str) -> None:
    if path.name == "audit.html":
        return
    if "/assets/track.js" not in text:
        fail(f"{path.relative_to(ROOT)}: missing /assets/track.js")
    if "calendly.com" not in text:
        return
    for match in re.finditer(r"<a\b[^>]*calendly\.com[^>]*>", text):
        tag = match.group(0)
        if "utm_source=rncld" not in tag or "utm_medium=site" not in tag:
            fail(f"{path.relative_to(ROOT)}: Calendly link missing rncld/site UTMs")
            break
        if "data-cta-id=" not in tag or "data-cta-position=" not in tag or "data-track=" not in tag:
            fail(f"{path.relative_to(ROOT)}: Calendly link missing data attributes")
            break
        if "utm_source=rncld.com" in tag or "utm_medium=website" in tag:
            fail(f"{path.relative_to(ROOT)}: Calendly link still uses the old UTM source or medium")
            break


def main() -> int:
    html_files = [
        p for p in local_files()
        if p.suffix == ".html" and "includes" not in p.relative_to(ROOT).parts
    ]
    for path in html_files:
        text = path.read_text(encoding="utf-8")
        blocks = check_jsonld(path, text)
        check_links(path, text)
        check_offer_name(path, text)
        check_tracking(path, text)
        check_nav(path, text)
        if 'href="/about.html"' in text or "href='/about.html'" in text:
            fail(f"{path.relative_to(ROOT)}: link points at /about.html; use /about/")
        if path.parent == ROOT / "blog" and path.name != "index.html":
            check_post(path, text, blocks)
    for path in (ROOT / "llms.txt", ROOT / "blog" / "README.md"):
        if path.is_file():
            check_offer_name(path, path.read_text(encoding="utf-8"))
    for path in (ROOT / "blog" / "posts").glob("*.md"):
        check_offer_name(path, path.read_text(encoding="utf-8"))
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

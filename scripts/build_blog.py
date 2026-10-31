#!/usr/bin/env python3
"""Build RAINCLOUD blog posts from Markdown (or HTML) sources.

Reads blog/posts/*.md, writes blog/<slug>.html, refreshes the card list in
blog/index.html, and upserts those URLs plus /problems/*/ and /about/ into sitemap.xml.

Usage (from the repo root):
    python3 scripts/build_blog.py
    python3 scripts/build_blog.py blog/posts/my-new-post.md
"""

from __future__ import annotations

import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

import yaml

ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "blog" / "posts"
BLOG_DIR = ROOT / "blog"
INDEX_PATH = BLOG_DIR / "index.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
PROBLEMS_DIR = ROOT / "problems"
ABOUT_DIR = ROOT / "about"

SITE = "https://rncld.com"
PUBLISHED_STAMP = "2026-10-31"
OG_IMAGE = f"{SITE}/assets/band-boardroom.png"

TOPICS = {
    "diagnosis": {
        "path": "/audit.html",
        "heading": "Not sure what to fix first?",
        "body": (
            "The 100-Point GTM Audit scores your go-to-market against 100 points "
            "and ranks every finding by what it\u2019s costing you in pipeline. "
            "$5,000, ten business days."
        ),
        "meta": "$5,000 \u00b7 10 business days \u00b7 required before any engagement",
        "button": "See the 100-Point GTM Audit",
        "secondary_label": "Book the audit call",
        "secondary_kind": "calendly",
    },
    "build": {
        "path": "/gtm-consulting.html",
        "heading": "Ninety days to rebuild the motion.",
        "body": (
            "The audit tells you what\u2019s broken and in what order. The engagement "
            "builds it \u2014 ICP, positioning, the pipeline model, outbound, the "
            "scorecard in your CRM and the playbook \u2014 in your tools, with the "
            "people who will run it after I\u2019m gone."
        ),
        "meta": "$5,000 audit \u00b7 $37,500 over 90 days \u00b7 $7,500/mo after",
        "button": "See the 90-day engagement",
        "secondary_label": "Book the audit call",
        "secondary_kind": "calendly",
    },
    "soft": {
        "path": "/resources/100-point-gtm-framework.html",
        "heading": "The 100-Point GTM Framework.",
        "body": (
            "Every point I score, published in full. It\u2019s the full list the "
            "audit scores against, so you can see exactly what it measures before "
            "you spend anything."
        ),
        "meta": "Free",
        "button": "Download the 100-point framework",
        "secondary_label": "Or see the 100-Point GTM Audit",
        "secondary_kind": "path",
        "secondary_path": "/audit.html",
    },
}

REQUIRED = (
    "title",
    "description",
    "slug",
    "date",
    "date_label",
    "read_time",
    "tag",
    "topic",
    "excerpt",
    "takeaways",
    "faqs",
)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def campaign_for(slug: str) -> str:
    return "blog_" + slug


def utm(slug: str, content: str, path: str | None = None) -> str:
    query = (
        "utm_source=rncld.com&amp;utm_medium=website&amp;utm_campaign="
        + esc(campaign_for(slug))
        + "&amp;utm_content="
        + esc(content)
    )
    if path is None:
        base = "https://calendly.com/30minutechat/30min"
        return base + "?" + query
    join = "&amp;" if "?" in path else "?"
    return path + join + query


def load_post(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---"):
        raise SystemExit(f"{path}: missing front matter")
    end = raw.find("\n---", 3)
    if end == -1:
        raise SystemExit(f"{path}: unterminated front matter")
    meta = yaml.safe_load(raw[3:end]) or {}
    body = raw[end + 4 :].lstrip("\n")
    if not isinstance(meta, dict):
        raise SystemExit(f"{path}: front matter must be a mapping")
    meta["body"] = body
    meta["source"] = path
    missing = [key for key in REQUIRED if not meta.get(key)]
    if missing:
        raise SystemExit(f"{path}: missing {', '.join(missing)}")
    if meta["topic"] not in TOPICS:
        raise SystemExit(f"{path}: topic must be diagnosis, build, or soft")
    faqs = meta["faqs"]
    if not isinstance(faqs, list) or not 3 <= len(faqs) <= 5:
        raise SystemExit(f"{path}: faqs must be a list of 3 to 5 items")
    for item in faqs:
        if not isinstance(item, dict) or not item.get("q") or not item.get("a"):
            raise SystemExit(f"{path}: each faq needs q and a")
    takes = meta["takeaways"]
    if not isinstance(takes, list) or not 3 <= len(takes) <= 6:
        raise SystemExit(f"{path}: takeaways must be a list of 3 to 6 strings")
    if meta.get("video"):
        for key in ("video_name", "video_description", "video_upload_date", "video_duration"):
            if not meta.get(key):
                raise SystemExit(f"{path}: video is set, so {key} is required")
    if Path(meta["slug"]).name != meta["slug"] or "/" in meta["slug"]:
        raise SystemExit(f"{path}: slug must be a single path segment")
    return meta


def youtube_id(url: str) -> str:
    patterns = (
        r"youtu\.be/([A-Za-z0-9_-]{6,})",
        r"[?&]v=([A-Za-z0-9_-]{6,})",
        r"youtube\.com/embed/([A-Za-z0-9_-]{6,})",
        r"youtube\.com/shorts/([A-Za-z0-9_-]{6,})",
    )
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise SystemExit(f"Could not read a YouTube id from {url}")


def render_markdown(source: str) -> str:
    """Small Markdown subset: headings, paragraphs, lists, quotes, links, emphasis."""
    lines = source.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<em>\1</em>", text)
        text = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda m: '<a href="' + m.group(2) + '">' + m.group(1) + "</a>",
            text,
        )
        return text

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(f"<h3>{inline(line[4:].strip())}</h3>")
            i += 1
            continue
        if line.startswith("## "):
            blocks.append(f"<h2>{inline(line[3:].strip())}</h2>")
            i += 1
            continue
        if line.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:].strip())
                i += 1
            blocks.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue
        if re.match(r"^[-*] ", line):
            items = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i]):
                items.append("<li>" + inline(lines[i][2:].strip()) + "</li>")
                i += 1
            blocks.append("<ul>\n" + "\n".join(items) + "\n</ul>")
            continue
        if re.match(r"^\d+\. ", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                item = re.sub(r"^\d+\. ", "", lines[i]).strip()
                items.append("<li>" + inline(item) + "</li>")
                i += 1
            blocks.append("<ol>\n" + "\n".join(items) + "\n</ol>")
            continue
        para = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{2,3} |[-*] |\d+\. |> )", lines[i]):
            para.append(lines[i].strip())
            i += 1
        blocks.append("<p>" + inline(" ".join(para)) + "</p>")
    return "\n\n".join(blocks)


def body_html(post: dict) -> str:
    if post.get("format") == "html":
        return post["body"].strip("\n")
    return render_markdown(post["body"])


def cta_html(post: dict, content: str) -> str:
    topic = TOPICS[post["topic"]]
    slug = post["slug"]
    primary = utm(slug, content, topic["path"])
    if topic["secondary_kind"] == "calendly":
        secondary = utm(slug, content)
        extra = ' target="_blank" rel="noopener"'
    else:
        secondary = utm(slug, content, topic["secondary_path"])
        extra = ""
    meta = f'\n        <p class="post-cta-meta">{esc(topic["meta"])}</p>' if topic.get("meta") else ""
    return f"""<div class="post-cta" data-cta-block="{esc(content)}">
        <h3>{esc(topic["heading"])}</h3>
        <p>{esc(topic["body"])}</p>{meta}
        <a href="{primary}" class="btn btn--primary" data-cta="{esc(content)}">
          <span>{esc(topic["button"])}</span>
          <svg class="btn-arrow" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </a>
        <p class="post-cta-sec"><a class="text-link" href="{secondary}"{extra}>{esc(topic["secondary_label"])}</a></p>
      </div>"""


def insert_inbody(article: str, snippet: str) -> str:
    matches = list(re.finditer(r"<h2\b", article))
    if len(matches) < 3:
        raise SystemExit("In-body CTA needs at least three h2 sections")
    index = matches[2].start()
    return article[:index] + snippet + "\n\n      " + article[index:]


def takeaways_html(post: dict) -> str:
    items = "\n".join(f"        <li>{esc(str(item))}</li>" for item in post["takeaways"])
    return f"""<aside class="takeaways" aria-label="Key takeaways">
        <div class="label label--accent">Key takeaways</div>
        <ol>
{items}
        </ol>
      </aside>"""


def video_html(post: dict) -> str:
    url = (post.get("video") or "").strip()
    if not url:
        return '<div class="post-video" data-video-slot="empty" hidden></div>'
    video_id = youtube_id(url)
    name = esc(post["video_name"])
    return f"""<figure class="post-video" data-video-slot="ready">
        <div class="yt-lite" data-id="{esc(video_id)}">
          <button type="button" class="yt-play" aria-label="Play video: {name}">
            <img src="https://i.ytimg.com/vi/{esc(video_id)}/hqdefault.jpg" alt="">
          </button>
        </div>
        <figcaption>{name}</figcaption>
      </figure>
      <script>
        document.querySelectorAll('.yt-lite').forEach(function(el) {{
          el.addEventListener('click', function() {{
            var id = el.getAttribute('data-id');
            var frame = document.createElement('iframe');
            frame.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1';
            frame.title = {json.dumps(post["video_name"])};
            frame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
            frame.allowFullscreen = true;
            el.replaceWith(frame);
          }});
        }});
      </script>"""


def faq_html(post: dict) -> str:
    blocks = []
    for item in post["faqs"]:
        blocks.append(
            "        <div class=\"faq-item\">\n"
            f"          <h3>{esc(str(item['q']))}</h3>\n"
            f"          <p>{esc(str(item['a']))}</p>\n"
            "        </div>"
        )
    inner = "\n".join(blocks)
    return f"""<section class="post-faq" aria-label="Questions">
        <h2>Questions this post answers</h2>
{inner}
      </section>"""


def related_html(post: dict, by_slug: dict) -> str:
    links = [
        f'        <li><a href="{esc(post["hub"])}">{esc(post["hub_label"])}</a></li>'
    ]
    for slug in post.get("related") or []:
        other = by_slug.get(slug)
        if not other:
            raise SystemExit(f"{post['slug']}: related slug {slug} was not found")
        links.append(
            f'        <li><a href="/blog/{esc(slug)}.html">{esc(other["title"])}</a></li>'
        )
    for item in post.get("also") or []:
        href = item["href"]
        label = item["label"]
        external = href.startswith("http")
        rel = ' target="_blank" rel="noopener"' if external else ""
        links.append(f'        <li><a href="{esc(href)}"{rel}>{esc(label)}</a></li>')
    inner = "\n".join(links)
    return f"""<nav class="post-related" aria-label="Related">
        <div class="label">On this topic</div>
        <ul>
{inner}
        </ul>
      </nav>"""


def json_ld(post: dict) -> str:
    slug = post["slug"]
    url = f"{SITE}/blog/{slug}.html"
    published = str(post["date"])
    modified = str(post.get("updated") or published)
    graph = [
        {
            "@type": "BlogPosting",
            "headline": post["title"],
            "description": post["description"],
            "image": OG_IMAGE,
            "author": {
                "@type": "Person",
                "name": "Colin Dowling",
                "url": f"{SITE}/about/",
            },
            "publisher": {
                "@type": "Organization",
                "name": "RAINCLOUD",
                "url": f"{SITE}/",
            },
            "mainEntityOfPage": url,
            "datePublished": published,
            "dateModified": modified,
            "articleSection": post["tag"],
            "inLanguage": "en",
        },
        {
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in post["faqs"]
            ],
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Articles", "item": f"{SITE}/blog/"},
                {"@type": "ListItem", "position": 3, "name": post["title"], "item": url},
            ],
        },
    ]
    if post.get("video"):
        video_id = youtube_id(post["video"])
        graph.append(
            {
                "@type": "VideoObject",
                "name": post["video_name"],
                "description": post["video_description"],
                "thumbnailUrl": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                "uploadDate": str(post["video_upload_date"]),
                "embedUrl": f"https://www.youtube.com/embed/{video_id}",
                "duration": post["video_duration"],
            }
        )
    payload = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def page_html(post: dict, by_slug: dict) -> str:
    slug = post["slug"]
    article = insert_inbody(body_html(post), cta_html(post, "inbody"))
    duplicate = ""
    if post.get("duplicate_of"):
        duplicate = (
            f"  <!-- Duplicate of {post['duplicate_of']}. "
            "Kept on rncld.com. Do not delete. "
            "rel=canonical points at the Ants URL. -->\n"
        )
    note = post.get("editorial_note") or ""
    note_html = f"  <!-- {note} -->\n" if note else ""
    title = post["title"]
    description = post["description"]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-041BP5G4HF"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', 'G-041BP5G4HF');
    document.addEventListener('click', function(e) {{
      var a = e.target.closest('a[href]');
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (!/\\/(audit|contact|gtm-consulting|resources)(\\.html)?(\\?|#|$)/.test(href) && href.indexOf('calendly.com') === -1) return;
      if (a.closest('nav') || a.closest('footer')) return;
      gtag('event', 'audit_cta_click', {{
        cta_text: (a.textContent || '').trim().slice(0, 100),
        cta_destination: href,
        cta_location: window.location.pathname
      }});
    }});
    document.addEventListener('DOMContentLoaded', function() {{
      var navToggle = document.getElementById('navToggle');
      var navLinks = document.getElementById('navLinks');
      if (!navToggle || !navLinks) return;
      navToggle.addEventListener('click', function() {{
        navLinks.classList.toggle('open');
        if (!navLinks.classList.contains('open')) {{
          navLinks.querySelectorAll('.has-dropdown.expanded').forEach(function(item) {{
            item.classList.remove('expanded');
          }});
        }}
      }});
      navLinks.querySelectorAll('a').forEach(function(a) {{
        a.addEventListener('click', function(e) {{
          var li = a.parentElement;
          var isDropdownParent = li && li.classList.contains('has-dropdown');
          var isMobile = window.innerWidth <= 768;
          var navOpen = navLinks.classList.contains('open');
          if (isDropdownParent && isMobile && navOpen) {{
            e.preventDefault();
            li.classList.toggle('expanded');
          }} else {{
            navLinks.classList.remove('open');
            navLinks.querySelectorAll('.has-dropdown.expanded').forEach(function(item) {{
              item.classList.remove('expanded');
            }});
          }}
        }});
      }});
    }});
  </script>
  <title>{esc(title)} — RAINCLOUD</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(post.get("duplicate_of") or f"{SITE}/blog/{slug}.html")}">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@200;300;400;500;600&family=Manrope:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/assets/site.css">
  <link rel="stylesheet" href="/assets/site-extra.css">
  <link rel="stylesheet" href="/assets/site-nav.css">
  <link rel="stylesheet" href="/assets/blog-post.css">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="RAINCLOUD">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:url" content="{esc(post.get("duplicate_of") or f"{SITE}/blog/{slug}.html")}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{OG_IMAGE}">
  <script type="application/ld+json">
{json_ld(post)}
  </script>
  <style id="rc-global">
    nav .nav-links a[aria-current="page"]{{color:var(--text-primary);}}
    footer.sf .sf-also{{margin-top:14px;font-size:.72rem;line-height:1.6;color:var(--text-tertiary);max-width:300px;}}
    footer.sf .sf-also a{{color:var(--text-secondary);border-bottom:1px solid var(--border-subtle);}}
    footer.sf .sf-also a:hover{{color:var(--text-primary);}}
  </style>
</head>
<body>
{duplicate}{note_html}  <nav id="nav" class="scrolled">
    <div class="container nav-inner">
      <a href="/" class="nav-logo">RAIN<em>CLOUD</em></a>
      <ul class="nav-links" id="navLinks">
        <li><a href="/audit.html">The Audit</a></li>
        <li><a href="/gtm-consulting.html">The Engagement</a></li>
        <li><a href="/pricing/">Pricing</a></li>
        <li><a href="/blog/" aria-current="page">Articles</a></li>
        <li><a href="/about/">About</a></li>
        <li><a href="{utm(slug, "nav")}" class="nav-cta" target="_blank" rel="noopener" data-cta="nav">Book the audit call</a></li>
      </ul>
      <button class="nav-toggle" id="navToggle" aria-label="Menu"><span></span><span></span><span></span></button>
    </div>
  </nav>

  <section class="post-hero">
    <div class="container--narrow" style="max-width: 720px;">
      <div class="label label--accent">{esc(post["tag"])}</div>
      <h1>{esc(title)}</h1>
      <div class="post-meta">
        <span><a href="/about/">Colin Dowling</a></span>
        <span>{esc(post["date_label"])}</span>
        <span>{esc(post["read_time"])}</span>
      </div>
    </div>
  </section>

  <div class="post-body">
    <div class="container--narrow" style="max-width: 720px;">
      {takeaways_html(post)}
      {video_html(post)}
      {article}
      {faq_html(post)}
      {cta_html(post, "post_end")}
      {related_html(post, by_slug)}
      <div class="post-nav">
        <a href="/blog/">&larr; All Posts</a>
        <a href="/blog/">See all articles &rarr;</a>
      </div>
    </div>
  </div>
  <footer class="sf">
    <div class="container">
      <div class="sf-top">
        <div>
          <div class="sf-logo">RAIN<em>CLOUD</em></div>
          <p class="sf-tag">One engagement: a 100-point GTM audit, a 90-day rebuild on a fee that steps down, then advisory. Run personally by Colin Dowling.</p>
          <p class="sf-also">Also from Colin Dowling: <a href="https://www.withants.com/" target="_blank" rel="noopener">Ants</a> (managed AI agents), <a href="https://www.friendlyghostwriter.com/" target="_blank" rel="noopener">Ghostwriter</a> (B2B content), The AI Ready Advisor (executive AI strategy).</p>
        </div>
        <div class="sf-cols">
          <div>
            <div class="sf-h">Work with me</div>
            <ul>
              <li><a href="/audit.html">The Audit</a></li>
              <li><a href="/gtm-consulting.html">The Engagement</a></li>
              <li><a href="/pricing/">Pricing</a></li>
            </ul>
          </div>
          <div>
            <div class="sf-h">Read</div>
            <ul>
              <li><a href="/blog/">Articles</a></li>
              <li><a href="/about/">About</a></li>
              <li><a href="/resources/100-point-gtm-framework.html">The 100-Point GTM Framework</a></li>
              <li><a href="/resources/benchmark-2026.html">2026 Benchmark Report</a></li>
              <li><a href="/llms.txt">llms.txt</a></li>
            </ul>
          </div>
          <div>
            <div class="sf-h">Talk</div>
            <ul>
              <li><a href="{utm(slug, "footer")}" target="_blank" rel="noopener" data-cta="footer">Book the audit call</a></li>
              <li><a href="/contact.html">Contact</a></li>
              <li><a href="mailto:colin@rncld.com"><!--email_off-->colin@rncld.com<!--/email_off--></a></li>
            </ul>
          </div>
        </div>
      </div>
      <div class="sf-copy">&copy; 2026 RAINCLOUD. All rights reserved.</div>
    </div>
  </footer>
</body>
</html>
"""


def card_html(post: dict) -> str:
    return f"""      <a href="/blog/{esc(post["slug"])}.html" class="blog-card">
        <span class="blog-tag">{esc(post["tag"])}</span>
        <div class="date">{esc(post["date_label"])}</div>
        <h2>{esc(post["title"])}</h2>
        <p>{esc(post["excerpt"])}</p>
        <span class="read">Read <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg></span>
      </a>"""


def index_ld(posts: list[dict]) -> str:
    items = []
    for position, post in enumerate(posts, start=1):
        items.append(
            {
                "@type": "ListItem",
                "position": position,
                "url": f"{SITE}/blog/{post['slug']}.html",
                "name": post["title"],
            }
        )
    payload = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "RAINCLOUD Articles",
        "itemListElement": items,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def replace_marked(text: str, start: str, end: str, inner: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = start + "\n" + inner.rstrip() + "\n      " + end
    if not pattern.search(text):
        raise SystemExit(f"Marker not found: {start}")
    return pattern.sub(replacement, text, count=1)


def update_index(posts: list[dict]) -> None:
    text = INDEX_PATH.read_text(encoding="utf-8")
    cards = "\n\n".join(card_html(post) for post in posts)
    text = replace_marked(text, "<!-- BLOG_CARDS:START -->", "<!-- BLOG_CARDS:END -->", cards)
    text = replace_marked(
        text,
        "<!-- BLOG_INDEX_LD:START -->",
        "<!-- BLOG_INDEX_LD:END -->",
        "  <script type=\"application/ld+json\">\n"
        + index_ld(posts)
        + "\n  </script>",
    )
    INDEX_PATH.write_text(text, encoding="utf-8")


def sitemap_url(loc: str, lastmod: str, changefreq: str, priority: str) -> str:
    return (
        "  <url>\n"
        f"    <loc>{xml_escape(loc)}</loc>\n"
        f"    <lastmod>{xml_escape(lastmod)}</lastmod>\n"
        f"    <changefreq>{changefreq}</changefreq>\n"
        f"    <priority>{priority}</priority>\n"
        "  </url>"
    )


def update_sitemap(posts: list[dict]) -> None:
    text = SITEMAP_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"  <url>.*?</url>", text, flags=re.S)
    kept = []
    for block in blocks:
        loc_match = re.search(r"<loc>(.*?)</loc>", block)
        if not loc_match:
            continue
        loc = loc_match.group(1)
        if loc == f"{SITE}/blog/":
            continue
        if loc.startswith(f"{SITE}/blog/") or loc.startswith(f"{SITE}/fix/") or loc.startswith(f"{SITE}/problems/") or loc == f"{SITE}/about/":
            continue
        kept.append(block)
    blog_index = sitemap_url(f"{SITE}/blog/", PUBLISHED_STAMP, "weekly", "0.7")
    post_blocks = []
    for post in sorted(posts, key=lambda item: item["slug"]):
        if post.get("duplicate_of"):
            continue
        lastmod = str(post.get("updated") or post["date"])
        post_blocks.append(
            sitemap_url(f"{SITE}/blog/{post['slug']}.html", lastmod, "monthly", "0.6")
        )
    extra_blocks = [sitemap_url(f"{SITE}/about/", PUBLISHED_STAMP, "monthly", "0.6")]
    if PROBLEMS_DIR.is_dir():
        for page in sorted(PROBLEMS_DIR.glob("*/index.html")):
            slug = page.parent.name
            extra_blocks.append(
                sitemap_url(f"{SITE}/problems/{slug}/", PUBLISHED_STAMP, "monthly", "0.8")
            )
    ordered = kept + [blog_index] + post_blocks + extra_blocks
    body = "\n".join(ordered)
    rebuilt = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )
    SITEMAP_PATH.write_text(rebuilt, encoding="utf-8")


def sort_key(post: dict):
    return (str(post["date"]), int(post.get("sort") or 0))


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv[1:]] or sorted(POSTS_DIR.glob("*.md"))
    if not paths:
        raise SystemExit(f"No posts in {POSTS_DIR}")
    posts = [load_post(path if path.is_absolute() else ROOT / path) for path in paths]
    # A partial file list still rebuilds every post so the index stays complete.
    if argv[1:]:
        posts = [load_post(path) for path in sorted(POSTS_DIR.glob("*.md"))]
    by_slug = {post["slug"]: post for post in posts}
    if len(by_slug) != len(posts):
        raise SystemExit("Duplicate slugs")
    for post in posts:
        if not post.get("hub") or not post.get("hub_label"):
            raise SystemExit(f"{post['slug']}: hub and hub_label are required")
        related = post.get("related") or []
        if len(related) < 2:
            raise SystemExit(f"{post['slug']}: list at least two related slugs")
    ordered = sorted(posts, key=sort_key, reverse=True)
    for post in ordered:
        target = BLOG_DIR / f"{post['slug']}.html"
        target.write_text(page_html(post, by_slug), encoding="utf-8")
        print(f"wrote {target.relative_to(ROOT)}")
    update_index(ordered)
    update_sitemap(ordered)
    print(f"updated {INDEX_PATH.relative_to(ROOT)} and {SITEMAP_PATH.relative_to(ROOT)}")
    print(f"built {len(ordered)} posts on {date.today().isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

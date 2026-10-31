# Adding a post

Posts are written as Markdown with YAML front matter in `blog/posts/`, then compiled to static HTML. DigitalOcean serves the HTML. Run the script before you commit.

```bash
python3 scripts/build_blog.py
```

That writes `blog/<slug>.html`, refreshes the cards on `blog/index.html`, and upserts the post plus `/problems/*/`, `/about/`, into `sitemap.xml`. A post with `duplicate_of` is left out of the sitemap and its `rel=canonical` points at that URL.

Check the result:

```bash
python3 scripts/validate_site.py
```

## Front matter

```yaml
---
title: The headline
description: Meta description, one or two sentences.
slug: my-new-post
date: 2026-11-01          # datePublished
date_label: November 2026
read_time: 6 min read
tag: Outbound             # the small label above the title
topic: diagnosis          # diagnosis | build | soft
excerpt: The card text on /blog/.
sort: 1                   # tie-break when two posts share a date; higher is newer
updated: 2026-11-01       # sitemap lastmod and dateModified
hub: /audit.html
hub_label: The 100-Point GTM Audit
related:                  # at least two other post slugs
  - outbound-reply-rates-2026
  - why-gtm-builds-fail
also:                     # optional extra links (problem pages, the other site)
  - href: /problems/outbound-not-landing/
    label: Outbound that gets no replies
takeaways:                # 3 to 6. Shown in the box at the top.
  - First takeaway.
  - Second takeaway.
  - Third takeaway.
faqs:                     # 3 to 5. Rendered on the page and as FAQPage JSON-LD.
  - q: The question?
    a: The answer, in words you are willing to have quoted.
video:                    # optional. Leave the key off until a video exists.
video_name:
video_description:
video_upload_date:        # YYYY-MM-DD
video_duration:           # ISO 8601, for example PT6M12S
---

The article, in Markdown.
```

`format: html` is only for the four posts that were retrofitted. Their bodies are the original HTML so the wording does not change. New posts should be Markdown. The converter supports paragraphs, `##` and `###`, `-` and `1.` lists, `>` quotes, `**bold**`, `*italic*`, and `[links](url)`.

## Topic decides both CTAs

| `topic` | When to use it | Button goes to |
| --- | --- | --- |
| `diagnosis` | The post is about something that is broken | `/audit.html` |
| `build` | The post is about building, hiring, or the process after handoff | `/gtm-consulting.html` |
| `soft` | The post should offer the free list, not a paid next step | `/resources/100-point-gtm-framework.html` |

The same block is inserted after the second section (before the third `h2`) and again at the end. Links carry `utm_source=rncld.com`, `utm_medium=website`, `utm_campaign=blog_<slug>`, and `utm_content=inbody` or `utm_content=post_end`.

## What the template always emits

- `BlogPosting`, `FAQPage` (the visible questions), and `BreadcrumbList` JSON-LD
- `VideoObject` only when `video` is set (`name`, `description`, `thumbnailUrl`, `uploadDate`, `embedUrl`, `duration`)
- A Key takeaways box
- A YouTube slot. It stays empty, and hidden, until `video` is a YouTube URL. The embed is a poster image that loads the iframe on click.
- A related list: the hub, two sibling posts, and any `also` links

Do not hand-edit `blog/<slug>.html`. The next build overwrites it.

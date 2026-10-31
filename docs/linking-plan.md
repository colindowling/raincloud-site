# Hub and spoke

Four hubs. Each one is a page that already exists. A post links up to its hub, across to two sibling posts, and to the problem page and offer that match the topic. Hubs link down to their spokes. Topic hubs at `/topics/` wait until a topic has three or more posts. Until then the problem page and the offer page are the hub.

Campaigns on blog CTAs: `utm_campaign=blog_<slug>` and `utm_content=inbody` or `post_end`.

Flow: post, then the problem page, then the offer, then the audit call.

## 1. Diagnose the motion

Pillar: [/audit.html](/audit.html) — 100-Point GTM Audit, $5,000, ten business days.

Spokes:

- [/blog/outbound-reply-rates-2026.html](/blog/outbound-reply-rates-2026.html) — topic `diagnosis`
- [/blog/bofu-content-that-moves-deals.html](/blog/bofu-content-that-moves-deals.html) — topic `diagnosis`
- [/problems/outbound-not-landing/](/problems/outbound-not-landing/) — offer: the audit
- [/problems/pipeline-not-growing/](/problems/pipeline-not-growing/) — offer: the audit. No post yet.

## 2. Rebuild and hand it over

Pillar: [/gtm-consulting.html](/gtm-consulting.html) — 90-Day GTM Fix, $37,500 over 90 days, then advisory at $7,500 a month.

Spokes:

- [/blog/why-gtm-builds-fail.html](/blog/why-gtm-builds-fail.html) — topic `build`
- [/problems/first-sales-hire/](/problems/first-sales-hire/) — offer: the engagement
- [/problems/founder-led-sales-trap/](/problems/founder-led-sales-trap/) — offer: the engagement

## 3. Read the score before you buy

Pillar: [/resources/100-point-gtm-framework.html](/resources/100-point-gtm-framework.html) — the free 100-point list. This is the `soft` destination.

Spokes:

- [/blog/claudeforce-for-hubspot.html](/blog/claudeforce-for-hubspot.html) — topic `soft`. Canonical points at the Ants copy. Not in the sitemap.
- [/resources/benchmark-2026.html](/resources/benchmark-2026.html)
- [/blog/bofu-content-that-moves-deals.html](/blog/bofu-content-that-moves-deals.html) — also linked here, because the unpaid next step is the framework

## 4. The fee

Pillar: [/pricing/](/pricing/). Not a content hub. Problem pages link here for the fee schedule.

## Author

Post bylines and `BlogPosting` author URLs point at [/about/](/about/). That page is Colin as the author: Person and AboutPage schema, a Modern Business Life link, and the audit-call button. It does not name past clients or employers. The older [/about.html](/about.html) is unchanged.

## Cross-site

[/blog/claudeforce-for-hubspot.html](/blog/claudeforce-for-hubspot.html) is the same article as [the Ants post](https://www.withants.com/blog/claudeforce-for-hubspot/). The page stays. `rel=canonical` points at the Ants URL, and the URL is omitted from `sitemap.xml`. That is the one cross-site link. The App Platform spec in this repo has no redirect rule, so this is a canonical rather than a 301.

## When a video exists

Set `video` in the post's front matter and rebuild. The page embeds that video and emits `VideoObject`. The YouTube description should link back to `https://rncld.com/blog/<slug>.html`. There is no video yet, so every slot is empty.

## Adding a spoke

1. Write the post (`blog/README.md`). Set `topic`, `hub`, and two `related` slugs.
2. If the post needs a problem page, clone `/problems/outbound-not-landing/` and keep prices, results, and competitor names to sentences already on the site. Put it at `/problems/<slug>/` and point the hero button at the offer in this plan.
3. Add the new URL here, and add a link on the hub page.
4. Run `python3 scripts/build_blog.py` and `python3 scripts/validate_site.py`.

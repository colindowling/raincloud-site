---
title: Your Outbound Didn't Stop Working. The Infrastructure Changed.
description: Cold email reply rates really have fallen, but most of the numbers being quoted are measuring different things. What the data actually shows, what changed in the inbox in 2024 and 2025, and what still works.
slug: outbound-reply-rates-2026
date: '2026-08-08'
date_label: August 2026
read_time: 9 min read
tag: Outbound
format: html
topic: diagnosis
sort: 3
updated: '2026-10-31'
hub: /audit.html
hub_label: The 100-Point GTM Audit
related:
- bofu-content-that-moves-deals
- why-gtm-builds-fail
also:
- href: /problems/outbound-not-landing/
  label: Outbound not landing
excerpt: Reply rates really have fallen — but most of the numbers being quoted measure different things. What the data actually shows, what changed in the inbox in 2024 and 2025, and the seven things that still move the number.
takeaways:
- The instinct is to blame the copy. It is almost never the copy.
- If you are going to quote a reply rate to your board, say what you divided by.
- If your reply rate fell off a cliff somewhere in 2024 or 2025 and never recovered, check your DNS records before you rewrite a single sentence of copy.
- A market where the best operators outperform the average by 8x is not a dead channel. It is a channel that stopped rewarding volume and started rewarding craft.
- If your reply rates fell and you have spent three months rewriting sequences, you have been debugging the wrong layer.
faqs:
- q: Did cold email reply rates actually collapse?
  a: Be careful with charts that show reply rates falling off a cliff. Most of those charts are stitched together from different vendors measuring different things. Belkins’ earlier report, covering 16.5 million emails, showed reply rates falling from 6.8% in 2023 to 5.8% in 2024, measured against people who opened the email. Their newer study, covering 7.5 million emails sent in 2025, reports 0.45% measured against everything sent. The same campaign can be described as 5% or 0.45% depending on which line you divide by.
- q: What should you say when you quote a reply rate?
  a: If you are going to quote a reply rate to your board, say what you divided by. Most people quoting these numbers cannot tell you.
- q: What do the credible 2025 and 2026 benchmarks show?
  a: Measured against total emails sent, Instantly reports a 3.43% average reply rate, with the top 10% of campaigns above 10.7%. Hunter.io reports 4.5% across all use cases and 3.0% for sales outreach, across 31 million emails. Sales.co reports a 2.09% reply rate across 2 million emails, of which only 14.1% were actually positive. Gong and 30 Minutes to President’s Club found the average rep now sends 344 cold emails per meeting booked.
- q: What should you check before rewriting the copy?
  a: If your reply rate fell off a cliff somewhere in 2024 or 2025 and never recovered, check your DNS records before you rewrite a single sentence of copy. A meaningful share of the “outbound stopped working” stories turn out to be a DMARC record that was never published.
- q: Is outbound dead?
  a: Outbound is not dead. It has become an infrastructure discipline wearing a copywriting costume. The teams still getting 10% replies are not writing better subject lines. They authenticated properly, they send less, they send from clean domains to smaller lists, and they pick up the phone.
---
<p>Every founder I talk to has the same story. The outbound motion that filled the calendar two years ago produces almost nothing now. Same list quality, same offer, often the same copy. A fraction of the replies.</p>

      <p>The instinct is to blame the copy. It is almost never the copy.</p>

      <h2>First, a warning about the numbers</h2>

      <p>You have probably seen a chart showing cold email reply rates falling off a cliff, from something like 8&ndash;12% a few years ago to under 1% today. Be careful with it. Most of those charts are stitched together from different vendors measuring different things, and the drop they show is partly an artifact of arithmetic rather than performance.</p>

      <p>Here is a concrete example. <a href="https://belkins.io/blog/cold-email-response-rates" target="_blank" rel="noopener noreferrer">Belkins</a> is one of the few agencies publishing benchmarks on a consistent panel. Their earlier report, covering 16.5 million emails, showed reply rates falling from 6.8% in 2023 to 5.8% in 2024. Their newer study, covering 7.5 million emails sent in 2025, reports 0.45%.</p>

      <p>That looks like total collapse. It is not. Between the two reports they changed the denominator. The first measured replies against people who <em>opened</em> the email. The second measures replies against <em>everything sent</em>. The same campaign can be described as 5% or 0.45% depending on which line you divide by.</p>

      <blockquote>If you are going to quote a reply rate to your board, say what you divided by. Most people quoting these numbers cannot tell you.</blockquote>

      <h2>What the data actually says</h2>

      <p>Measured against total emails sent, the credible 2025&ndash;2026 platform benchmarks cluster in a fairly tight band:</p>

      <ul>
        <li><strong>3.43%</strong> average reply rate, with the top 10% of campaigns above 10.7% &mdash; <a href="https://instantly.ai/cold-email-benchmark-report-2026" target="_blank" rel="noopener noreferrer">Instantly</a>, drawn from platform-wide data.</li>
        <li><strong>4.5%</strong> across all use cases, but only <strong>3.0%</strong> for sales outreach specifically &mdash; <a href="https://hunter.io/the-state-of-cold-email/" target="_blank" rel="noopener noreferrer">Hunter.io</a>, 31 million emails.</li>
        <li><strong>2.09%</strong> reply rate, of which only 14.1% were actually positive &mdash; <a href="https://sales.co/research/cold-email-statistics" target="_blank" rel="noopener noreferrer">Sales.co</a>, across 2 million emails. That is roughly one interested human per 157 contacts. Another 45% of their replies were out-of-office autoresponders.</li>
      </ul>

      <p>And the number that matters most to anyone building a team: analysis of 85 million cold emails by <a href="https://www.gong.io/blog/does-cold-email-even-work-any-more-heres-what-the-data-says" target="_blank" rel="noopener noreferrer">Gong and 30 Minutes to President's Club</a> found the average rep now sends <strong>344 cold emails per meeting booked</strong>.</p>

      <p>So the decline is real. It is just less dramatic, and better documented, than the version in the LinkedIn posts. What deserves your attention is not the size of the drop. It is the three things underneath it, because two of them are infrastructure problems you can actually fix.</p>

      <h2>Change one: authentication stopped being optional</h2>

      <p>On 1 February 2024, Google and Yahoo began enforcing new requirements on anyone sending more than 5,000 messages a day to consumer inboxes. SPF <em>and</em> DKIM, a published DMARC record, alignment between your From: domain and your authentication, one-click unsubscribe on marketing mail, and a spam complaint rate held below 0.3%.</p>

      <p>Google's own guidance is that you should target <strong>below 0.1%</strong> and never let it touch 0.3%. From June 2024, senders above that line became ineligible for delivery mitigation. In plain terms: cross it and there is no one to appeal to. Google's documentation notes a further enforcement ramp from November 2025, with non-compliant traffic facing outright rejection.</p>

      <p>Microsoft followed. In <a href="https://techcommunity.microsoft.com/blog/microsoftdefenderforoffice365blog/strengthening-email-ecosystem-outlook%E2%80%99s-new-requirements-for-high%E2%80%90volume-senders/4399730" target="_blank" rel="noopener noreferrer">April 2025 it announced</a> the same authentication requirements for high-volume senders to Outlook.com, enforced from 5 May 2025. Notably, Microsoft revised its plan mid-announcement: instead of routing non-compliant mail to Junk, it rejects it outright with a 550 5.7.515 error. Safe-sender lists do not override this.</p>

      <p>If your reply rate fell off a cliff somewhere in 2024 or 2025 and never recovered, check your DNS records before you rewrite a single sentence of copy. A meaningful share of the "outbound stopped working" stories I hear turn out to be a DMARC record that was never published.</p>

      <h2>Change two: the inbox itself got harder to reach</h2>

      <p>Authentication is table stakes. Placement is the harder problem. <a href="https://www.validity.com/wp-content/uploads/2025/03/2025-Benchmark-Report-FINAL.pdf" target="_blank" rel="noopener noreferrer">Validity's benchmark</a>, which uses seed-address testing rather than sender-reported data, put global inbox placement at 83.5% for 2024, with 6.7% going to spam and nearly 10% disappearing entirely.</p>

      <p>The trend inside that year is the part worth noting. Spam placement roughly doubled over 2024, from 4.5% in the first quarter to 8.6% in the fourth. Gmail placement fell almost five points across the same period as its filters were retrained.</p>

      <p>And the providers are not equivalent. Microsoft is the hard one: 75.6% inbox, 14.6% spam, against Gmail's 87.2% and 6.8%. If your ICP skews enterprise, you are disproportionately sending into Outlook tenants, which means the benchmark you should be measuring yourself against is materially worse than the global average.</p>

      <h2>Change three: everyone got a sending machine</h2>

      <p>The third change is simple saturation. AI writing tools removed the effort that used to cap volume. <a href="https://6sense.com/science-of-b2b/the-2025-science-of-b2b-bdr-benchmark-succeeding-in-a-changing-landscape/" target="_blank" rel="noopener noreferrer">6sense's BDR survey</a> found 62.5% of BDRs now use AI email writing tools, and that the average number of attempts per contact rose from 17 to 21 in a single year.</p>

      <p>Nobody's buyer got 24% more patient in that period.</p>

      <p>Worth being honest about the evidence here: this one is directionally obvious but poorly measured. I could not find a credible study quantifying the total increase in global cold email volume, and anyone who quotes you a precise figure for it is guessing.</p>

      <h2>The uncomfortable part</h2>

      <p>Averages hide the real story, which is dispersion. In that 85-million-email Gong dataset, the top 10% of reps booked <strong>8.1 times</strong> more meetings than the average rep. Top-decile campaigns still clear 10% reply rates while the average sits near 3%.</p>

      <p>A market where the best operators outperform the average by 8x is not a dead channel. It is a channel that stopped rewarding volume and started rewarding craft. That is uncomfortable if your motion was built on volume, which most were, because for about a decade volume was the cheapest thing to buy.</p>

      <h2>What actually moves the number</h2>

      <p>In rough order of return on effort:</p>

      <ol>
        <li><strong>Fix authentication first.</strong> SPF, DKIM, DMARC, alignment, one-click unsubscribe. This is a half-day of work and it is the difference between being delivered and being rejected.</li>
        <li><strong>Turn off open tracking.</strong> Hunter found sequences without tracking pixels saw reply rates of 7.4% against 4.4% with them &mdash; a 68% difference. Belkins ran the same experiment and measured about three percentage points. The pixel is a deliverability liability, and open rates have been unreliable since Apple Mail Privacy Protection anyway. You are trading a real outcome for a fake metric.</li>
        <li><strong>Send from a real domain.</strong> Custom-domain sending outperformed freemail 5.2% to 2.5% in Hunter's data.</li>
        <li><strong>Cut list size.</strong> Lists of 21&ndash;50 recipients replied at 6.2%; lists over 500 at 2.4%. Same senders, same tooling.</li>
        <li><strong>Cap daily volume per inbox.</strong> 20&ndash;49 sends per day per account correlated with 27% higher reply rates than heavier sending.</li>
        <li><strong>Stop sending email on its own.</strong> Gong's analysis of 300 million calls found email-only sequences replied at 1.81%, while sequences paired with cold calling hit 3.44%. Leaving a voicemail moved email replies from 2.73% to 5.87%. The phone is not a separate channel; it is what makes the email work.</li>
        <li><strong>Reconsider who you are targeting.</strong> C-level contacts are 30.2% less likely to reply than non-executives. Companies under 50 people reply at roughly double the rate of enterprises, and their replies are far more likely to be positive &mdash; 18.2% positive for companies under 10 people, against 3.4% for those over 5,000.</li>
      </ol>

      <h2>The honest summary</h2>

      <p>Outbound is not dead. It has become an infrastructure discipline wearing a copywriting costume. The teams still getting 10% replies are not writing better subject lines than you. They authenticated properly, they send less, they send from clean domains to smaller lists, and they pick up the phone.</p>

      <p>If your reply rates fell and you have spent three months rewriting sequences, you have been debugging the wrong layer.</p>

      

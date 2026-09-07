---
description: One publish-ready blog post from a keyword-map row — paste-ready for Hibu, researched, cited, in a tax-firm voice
argument-hint: "[keyword, optional — pulls the next row from keyword-map.md]"
---

Draft one blog post. Keyword: $ARGUMENTS

**This site runs on Hibu, so nothing here writes to a repo and nothing deploys.** The output is
one markdown file in `page-drafts/` holding the finished post plus its metadata, ready to paste
into Hibu's editor or hand to Hibu support.

## ⛔ THE VOICE RULE

The register is a competent professional explaining something clearly to a worried person.
Warm, plain, direct. This is a firm that handles people's tax filings, and the reader is often
anxious, behind, or afraid of getting something wrong. Confidence and clarity are what convert
here — not personality.

**Hard rules:**

- **Plain words over jargon, every time.** If a term must appear because the reader will search
  it, define it in the same sentence. Never use an IRS form number without saying what it does.
- **Answer first, explain second.** The reader came with a question. Give the answer in the first
  40 to 50 words, then earn the rest of the page.
- **No jokes, no bits, no cute framing.** Dry warmth in a single aside is fine. A punchline about
  someone's late books or their tax bill is not. The reader is stressed about money and the law.
- **Never minimize a real risk to sound reassuring.** "It is fixable" is true and useful.
  "It is no big deal" is neither.
- **No fear-selling.** Do not manufacture urgency out of penalties or audits. State the actual
  consequence plainly, once, and move to what to do about it.
- **Second person, active voice, short sentences.** Say "you owe" not "taxes are owed by you".

## Read first

`references/blog-post-retention.md` — the retention rules that matter most here: a subhead every
150 to 300 words, the answer in the first 40 to 50 words, and a mid-text call to action, which
does most of the converting. Also `references/hub-spoke-pages.md` when the map row is a hub or a
spoke: a hub is a short router with an H2 per spoke, and it grows a section the day any new spoke
ships; a spoke takes one subtopic deep, never the hub's head term, and names its hub early.

## Which keyword

Never ask. Take the next unwritten `## N. Blog post:` row in `keyword-map.md`, lowest N, skipping
anything already in `website-index.md`. A named argument overrides. Map empty of blog rows? Take
the best saved-for-later keyword under the ceiling in the map header. State the pick in one line
and start.

## The work

1. **Spec.** Read the top 3 organic results — word count, H2 outline, tables, FAQs. Target their
   average give or take 20 percent, plus THE GAPS none of them cover.
2. **Research, and cite it.** Gather from the ranking articles, primary sources (IRS, the
   California Franchise Tax Board, the Secretary of State), and real practitioner writing.
   **Every statistic carries a live link to its source.** An attribution with no link is not a
   citation. If a figure cannot be sourced and linked, it does not ship — swap it for one that
   verifies. See `references/citations.md`.
   **Tax facts carry a date.** Rules, thresholds, deadlines and fees change every year. Name the
   tax year the figure applies to, in the sentence, and link the primary source rather than a
   blog quoting it.
3. **Buyer.** Name the ONE person this post is for in a sentence — who they are, what they fear,
   what they typed into Google — and write to them.
4. **Write into the skeleton** in `references/blog-post-template.md`: quick answer, proof line,
   main table, cluster H2s, field section, FAQ, bridge call to action, author box. One H2 per
   secondary keyword on the map row.
5. **⛔ Never invent proof.** Ask the user for real client numbers, reviews and credentials before
   writing, and use only what they give you. Missing proof becomes a marked
   `[NEEDS FROM YOU: …]` line, never a plausible-sounding figure. Do not write "CPA" unless a CPA
   is on staff. Do not offer or imply IRS representation, payroll or ITIN work — all on the DON'T
   list in "## My setup".
6. **The compliance read.** Before finishing, reread every sentence that states a tax rule, a
   deadline, a dollar threshold or an eligibility test. Each one is either sourced and dated, or
   it is softened to general guidance with a line telling the reader their situation decides it.
   A blog post that gets a rule wrong costs a client money and costs the firm its credibility.
7. **Images.** A hero plus one visual per roughly 350 words. Specify each in words. Body images
   show the work, a document, or a diagram — never a stock face used as decoration. A face appears
   only in the author box, and only if it is the real author.
8. **On-page.** Follow `references/on-page-seo.md`. Give 2 to 3 title and meta description
   variants per `references/meta-info.md` and say which you would pick and why.

## Finish

Save to `page-drafts/blog-<slug>.md`. Then:

- Append a block to `website-index.md` with status **Draft**.
- MOVE the whole map row into `# Written` in `keyword-map.md`, keeping its number. Never add a
  status field to the map.
- Name every internal link the post needs and every existing page that should link TO it. On
  Hibu those are separate manual edits, so list them or they will not happen.
- Say in one line what proof is still missing and what the post cannot claim without it.

Never report the post as published, ranked or submitted.

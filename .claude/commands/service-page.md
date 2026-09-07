---
description: One money page from a keyword-map row — a paste-ready page brief for Hibu, proof-first, never invented
argument-hint: "[service or service+city keyword, optional]"
---

Draft one money page. Keyword: $ARGUMENTS

**This site runs on Hibu, so nothing here writes to a repo and nothing deploys.** The output
is one markdown file in `page-drafts/` containing everything needed to build the page inside
Hibu's editor or to hand to Hibu support: metadata, the full copy section by section, image
direction, internal links, and the schema block. Never claim a page is live. It is live when
the user says it is live.

## Step 0 ⛔ The page budget — FIRST RUN ONLY

Read `CLAUDE.md` "## My setup". If `HIBU_PAGE_BUDGET` is recorded (a recorded "unknown" counts),
say nothing and go straight to the page. If it is missing, ask this and nothing else:

> "One thing before I draft money pages. Hibu's terms cap managed page builds at 4 new pages
> per service year on most packages, with 5 or 10 more as a paid add-on — but the Smart Sites
> editor lets some customers add pages themselves. Which are you on, and how many pages can you
> actually publish before January? If you do not know, ask Hibu and I will draft in the meantime."

Record the answer in "## My setup" so it is never asked twice. If the budget is smaller than the
number of deadline pages on the map, say so plainly and say which rows you would build with the
budget available — never quietly draft 19 pages that cannot be published.

## Which page

Never ask. No argument = the next unwritten `## N. Service page:` row in `keyword-map.md`,
lowest N, hubs before their city spokes. A named argument overrides. Skip anything already
listed in `website-index.md`. All rows written? Say so and point at `/keyword-research expand`.

State the pick in one line, then work.

## The words

1. **Spec.** Search the primary keyword and read the top 3 organic results — format, length, H2s,
   and the trust elements they show. If a map pack shows, the conversion model comes from the
   map-pack businesses, not the organic 10. Finish the spec with THE GAPS: what none of them do
   that this page will.
2. **Buyer.** Name the ONE person this page is for in a sentence — who they are, what they fear,
   what they typed into Google. Their fears become the FAQ. Their words become the copy.
3. **⛔ Proof-first, and never invent one.** Every claim traces to something the user gave you.
   Before writing a word, ask for the real numbers, reviews, credentials, licences, years in
   business and prices. Quote reviews word for word. If a proof point is missing, leave a clearly
   marked `[NEEDS FROM YOU: …]` line in the draft — never a plausible placeholder number, never a
   rounded guess, and never a credential the business has not earned. On this site that matters
   more than usual: do not write "CPA" unless a CPA is on staff, and do not imply IRS
   representation, payroll or ITIN work, which are all on the DON'T list in "## My setup".
4. **City pages are never clones.** Read `references/doorway-pages.md` before any city page and
   apply its local-material test. Localize the PROBLEM, not the place: different client mix,
   different local filing quirks, real jobs done in that city, city-specific FAQ answers. If there
   is no real local material for a city, say so and skip it rather than swapping a name. Read
   `references/hub-spoke-pages.md` before any hub or city page — the hub's "Areas we serve"
   section grows a passage and a link for every city the same day that city page ships.
5. **Images.** Specify each slot in words: what the photo shows, where it sits, and what it must
   never be. Real client work and real team photos only. Never a stock face presented as a person
   from the business. Faces appear only in a team or about slot, never the hero.

## ⛔ Less is more — default to collapsed

A money page is sales copy, not a document. Full rule in `references/service-page-template.md`.
Only these stay open: the H1 and hero promise, the offer and price, ONE proof line, every call to
action and the form, and one line naming the service area. Everything else — the proof stack,
what is included, the process, jobs done, tables and every FAQ answer — goes in an accordion.
Accordion content is indexed normally, so this costs nothing in rankings.

The test: picture the page with every accordion shut. If that does not sell on its own, cut a
line or promote one. Never open a section back up to fix it.

## On-page

Follow `references/on-page-seo.md`. Give 2 to 3 title and meta description variants per
`references/meta-info.md`, and say which you would pick and why. The primary keyword is the H1
and the title, once. Every secondary keyword from the map row gets its own H2 section — if you
cannot picture a real section for one, say so rather than padding.

Include a LocalBusiness or Service schema block as JSON-LD, ready to paste, with only facts the
user confirmed.

## Finish

Save to `page-drafts/service-<slug>.md`. Then:

- Append a block to `website-index.md` with status **Draft**.
- MOVE the whole map row into `# Written` in `keyword-map.md`, keeping its number. Never add a
  status field to the map — a block's section IS its status.
- List every internal link the page needs, and every existing page that must gain a link TO it.
  On Hibu those are separate edits, so name them explicitly or they will not happen.
- Say in one line what proof is still missing and what the page cannot claim until it arrives.

Never report the page as published, ranked or submitted. Handing it to Hibu is the user's step.

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## My setup

Used by `/keyword-research` (and any later SEO command) so these are never asked twice.

- **Business:** Top Tax Pros — tax preparation, bookkeeping, business entity setup.
- **Do NOT map:** ITIN applications, payroll, IRS resolution / audit representation, standalone tax planning or advisory. Confirmed 2026-09-07.
- **Market:** Lakewood, CA and neighboring cities (Long Beach, Cerritos, Bellflower, Downey and nearby). Customers search from the US.
- **Semrush database:** `us`.
- **Business type:** local brand. Service × city is the map's axis; national volume is never their addressable demand.
- **Domain:** toptaxpros.com. Authority Score 9 (2026-09-07), so the difficulty ceiling is a flat 30.
- **Owner / author byline:** Brian Cook, CTEC A045646, registered since 2003. Firm founded 2000. **Standard tenure claim in copy: "over 20 years of service."** Blog posts are bylined to him, not to the company — CTEC registers individuals, and the credential posts argue for checking a named preparer.
- **Proof line (confirmed 2026-09-07):** 4.9 stars across 684 Google reviews. Cite Google, not Yelp.
- **Also sells, not on the map:** crypto tax preparation. The keyword family sits above the difficulty ceiling and is held by software companies — revisit as Authority Score climbs.
- **Contact:** (562) 600-7072 · 5261 Paramount Blvd, Lakewood, CA 90712 · Mon–Fri 9am–8pm, Sat 10am–3pm (confirm hours). Two stale phone numbers are still live in third-party directories.
- **Pricing (confirmed 2026-09-07):** monthly bookkeeping in three flat tiers, no hourly overages — Essentials $350/mo (2 accounts, 100 transactions), Standard $550/mo (4 accounts, 250 transactions, payroll import, quarterly call), Full $750/mo (6 accounts, 450 transactions, inventory, monthly call); above that, quoted. Client pays for their own QuickBooks subscription, in their name. Cleanup and catch-up $250/hour, one hour minimum. Personal returns typically $295 (from $250). Self-employed/single-member LLC from $445. Corporate/S-corp from $950. Non-profit returns $500. Non-profit formation $750. Statement of Information filing $100 plus the state fee. **Invoicing runs through GoHighLevel, not QuickBooks — QuickBooks has no sales data.** QuickBooks file review free. Turnaround: every cleanup finished in 14 business days or less — a ceiling, not an average. This is a premium position — pages argue outcome, speed and continuity, never price.
- **Platform:** Hibu. No repo, no file-based publishing, no deploy step. Pages are drafted to `page-drafts/` and built inside Hibu's editor or handed to Hibu support.
- **HIBU_PAGE_BUDGET:** 19 pages, confirmed 2026-09-07. Slate and schedule in `page-drafts/PUBLISHING-PLAN.md`. Note page 5 is a rewrite of the live `/business-accounting` page and does not consume a slot.
- **Busy season:** January through May. Everything with seasonal demand must be live and aged before the January ramp, so the writing window is roughly September through December.
- **Credential (confirmed 2026-09-07):** CTEC-registered tax preparers, **CTEC A045646**. **No CPA and no enrolled agent on staff**, so no *unlimited* IRS representation rights. **Brian Cook does hold an IRS Annual Filing Season Program Record of Completion**, which carries *limited* rights: representation before IRS revenue agents, customer service and the Taxpayer Advocate Service, only on returns he prepared and signed, and never before appeals or collections. He is listed in the IRS Directory of Federal Tax Return Preparers. Record of Completion confirmed current for each filing year (2026-09-07). State the limits whenever the rights are mentioned. **This claim decays: it must be renewed every year, and if it ever lapses the representation language comes off the pages.** Never write "CPA", "public accountant" or any variant as a description of the firm — in copy, metadata, or schema markup. Use `ProfessionalService` or `TaxPreparationService` schema types, never `AccountingService`.
- **The word "accountant" is restricted in California.** B&P Code 5058 bars titles likely to be confused with CPA or public accountant, and the Board's regulation reached "accountant" and "accounting" generally. *Moore v. California State Bd. of Accountancy* (1992) 2 Cal.4th 999 narrowed that: the terms may be used where a modifier or express disclaimer dispels confusion about licence status. Any page using them needs that disclaimer above the fold and a legal read first.
- **"Bookkeeper" and "bookkeeping" are NOT restricted in California.** No licence is needed to use them, and CTEC registration covers paid tax return preparation, not bookkeeping. The whole bookkeeping side of the map is claimable without disclaimers.
- **Writing about CPAs and enrolled agents is fine and encouraged.** Blog posts explaining what a CPA costs or how the credentials differ are honest and they are the cheapest rankings available. The line is describing the firm, not discussing the profession.
- **Never claim:** unlimited IRS representation, appeals or collections work, payroll, or ITIN work.

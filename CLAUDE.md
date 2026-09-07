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
- **Platform:** Hibu. No repo, no file-based publishing, no deploy step. Pages are drafted to `page-drafts/` and built inside Hibu's editor or handed to Hibu support.
- **HIBU_PAGE_BUDGET:** unknown — Hibu's terms cap managed builds at 4 new pages per service year on most packages, with 5 or 10 more as a paid add-on, but Smart Sites customers can add pages themselves. Confirm with Hibu before drafting past the budget.
- **Busy season:** January through May. Everything with seasonal demand must be live and aged before the January ramp, so the writing window is roughly September through December.
- **Never claim:** "CPA" unless a CPA is on staff, and no IRS representation, payroll or ITIN work.

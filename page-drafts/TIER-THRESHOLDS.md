# Suggested transaction thresholds — and why the first set was wrong

## The problem with the tiers I proposed

Price scales roughly **1× → 2× → 3.4×** ($250, $500, $850).

The volumes I proposed scale **1× → 3× → 7.5×** (100, 300, 750 transactions).

Work does not scale slower than volume, so the ladder was upside down. The top tier was the worst
of the three — it asked for seven and a half times the volume at three and a half times the price.
With no overages, every Full-tier client would have been subsidised by the Essentials clients.

That is my error, and it is much cheaper to catch now than after someone signs a twelve-month
relationship at the wrong price.

---

## What a month of bookkeeping actually takes

Rough throughput for competent work in QuickBooks Online with connected feeds and trained
categorization rules:

| Task | Time |
|---|---|
| Categorization and review, once rules are trained | 100–150 transactions an hour |
| Reconciling one account | 10–20 minutes |
| Producing and reviewing the monthly reports | 15–20 minutes |
| Client questions and back-and-forth | 10–30 minutes, highly variable |

**Applied to the tiers I proposed:**

| Tier | Implied by price | Actually takes | Verdict |
|---|---|---|---|
| $250 · 2 accounts · 100 txns | 1 hour | ~1.25–1.5 hrs | Slightly over |
| $500 · 4 accounts · 300 txns | 2 hours | ~3–3.5 hrs | Well over |
| $850 · 8 accounts · 750 txns | 3.4 hours | ~7–8 hrs | Roughly double |

---

## Suggested replacement

| Tier | Price | Accounts | Transactions/month | Target hours |
|---|---|---|---|---|
| Essentials | $250 | Up to 2 | Up to 75 | ~1 |
| Standard | $500 | Up to 4 | Up to 200 | ~2 |
| Full | $850 | Up to 6 | Up to 400 | ~3.5 |

Above 400 transactions or 6 accounts, quoted individually.

Work now scales with price. The tiers are still competitive — a $199 provider bounding at 100
transactions is common — and the difference is that yours will still be profitable in month
eighteen.

---

## Two things that protect the flat price more than the thresholds do

**1. Charge a setup fee.** The first two or three months of any new client are two to three times
slower than the steady state: categorization rules are untrained, the chart of accounts usually
needs work, and opening balances have to be tied out. A flat monthly price with no onboarding fee
means you eat that every single time you win a client, and you win it back only if they stay a
year.

A one-time setup fee of roughly one to two hours at your rate — call it $250 to $500 — covers the
ramp and is completely standard in this market. It also filters out the shoppers.

**2. The real variable is mess, not volume.** A 60-transaction month with personal spending run
through the business account, untagged transfers between accounts, and a client who answers emails
in a fortnight takes longer than a clean 200-transaction month. Transaction count is the only
variable a buyer can self-assess, which is why it belongs on the page — but the scope line should
also say the tier assumes a business bank account used for business, and that untangling personal
spending is cleanup work.

---

## Which tier will most clients actually land in

Typical monthly transaction counts by business type:

| Business type | Transactions/month | Tier |
|---|---|---|
| Solo consultant, freelancer, single-owner trade | 20–60 | Essentials |
| Small service business, 1–5 staff — contractor, salon, landscaper | 75–200 | Standard |
| Small professional practice | 50–150 | Essentials or Standard |
| Restaurant, bar, retail with a point-of-sale system | 400–1,500+ | Above Full, quoted |
| Ecommerce | 200–1,000+ | Full or quoted |

**The likely median for your client base is 100 to 200 transactions a month, which is Standard,
not Essentials.**

That has three consequences worth planning around:

1. **$250 is the advertised entry price, not the expected sale.** Essentials fits solo operators
   and side businesses. A contractor with two employees and a work truck is already past it.
   That is a normal and healthy shape — the low tier earns the click, the middle tier earns the
   revenue.
2. **Expect an average of roughly $450 to $550 a month per client**, assuming most land in
   Standard with a tail in each direction. Against a 26-year local reputation and a 4.5-star
   rating, that is a solid recurring base.
3. **Restaurants and retail do not fit the ladder at all.** A point-of-sale system generates more
   transactions in a week than Essentials allows in a month. Either quote them individually or say
   on the page that high-volume retail and hospitality are quoted separately — otherwise you will
   field enquiries from businesses the tiers cannot serve, and the flat-price promise makes
   underquoting them expensive.

## How to check these cheaply

Time three real client months end to end — one small, one medium, one large — including the
questions and the report review, not just the categorization. Three data points from your own
practice beat every estimate on this page.

**QuickBooks was checked on 2026-09-07 and cannot answer this.** The connection works and the
company is correct, but there is no sales data in it:

| Checked | Result |
|---|---|
| Invoices, Jan 2023 to Sep 2026 | 0 |
| Sales by customer, last 12 months | No data |
| Sales by product or service, last 12 months | No data |
| Recurring invoice templates | 0 |
| Service items | 2 — "Services" and "Hours", neither with a price set |

So the estimates above stand as the best available answer, and they remain estimates. The only way
to replace them with fact is to time three real client months.

**This has a consequence beyond pricing.** Two of the automation commands in this repo,
`/ghl-ar-collections` and `/ghl-owner-scorecard`, read revenue and receivables from QuickBooks.
With no invoices in the file, both will return nothing. If billing runs somewhere else — Square
appears in this workspace but is not authorized — those plays need pointing at it instead.

**These numbers are inferred from general bookkeeping throughput, not measured on your team.**
If your rules are unusually well built or your clients unusually clean, you can carry more volume
than this. Do not raise the thresholds on optimism, though — with no overages, a wrong threshold
is a monthly loss for the life of the client.

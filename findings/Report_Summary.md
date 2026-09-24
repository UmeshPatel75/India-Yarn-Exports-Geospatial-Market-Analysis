# India's Yarn Exports — Destination Analysis, 2017-18 to 2025-26

**Nine years of India's cotton and man-made yarn exports, analysed by
destination, product and concentration risk**

US$ 4,278 million in FY 2025-26 · 130 destination markets ·
three HS headings · 3,121 destination-year records

*Source: Directorate General of Commercial Intelligence and Statistics
(DGCI&S), Ministry of Commerce & Industry. Values FOB in US$ million.*

---

## Why this analysis

I spent eight years exporting textile yarns from Surat, first as a
senior sales manager and then running a trading partnership. The
question that mattered commercially was always the same: which markets
are worth developing, and how exposed are we if one of them closes.

Public trade data answers that question, but not in the form the
portal provides it. Tradestat gives you a year at a time, a heading at
a time, with no growth decomposition and no concentration measure.
This project assembles nine years across three headings and asks what
an exporter would actually want to know.

**Stack:** Python (pandas, plotly) for extraction and analysis, Power
BI for the reporting layer, 24 manual downloads reshaped into a single
tidy dataset.

---

## Headline: the aggregate index is misleading

India's yarn exports look diversified. The combined Herfindahl-
Hirschman Index for FY 2025-26 is **1,414 — "competitive"** on the
conventional scale, comfortably below the 1,500 threshold.

Disaggregate by heading and that picture falls apart.

| Heading | 2017-18 | 2025-26 | Change | Top market now |
|---|---|---|---|---|
| **5205 Cotton yarn** | 1,204 | **2,209** | **+83%** | Bangladesh **43.3%** |
| 5402 Synthetic filament | 1,303 | 696 | −47% | Turkey 18.2% |
| 5509 Synthetic staple | 992 | 690 | −30% | Turkey 16.4% |
| **Combined** | 774 | 1,414 | +83% | Bangladesh 33.6% |

**Cotton yarn concentration nearly doubled and is approaching the
2,500 "highly concentrated" threshold. Both synthetic categories moved
the opposite way — they diversified.** Neither leans on Bangladesh at
all; their largest market is Turkey at under 19%.

The combined index reads "competitive" because two diversifying
categories mask one concentrating fast. An exporter reading only the
aggregate would conclude the risk had not changed. It has, and it sits
entirely in the largest category.

**This is the finding of the project**, and it exists only because the
analysis was run per heading rather than on the chapter total.

---

## The customer changed, the dependence did not

In 2017-18 China was India's largest yarn destination at 16.9% of
value, rising to 22.7% the following year. From 2019-20 onward
Bangladesh has held the top position every year, reaching **37.7% in
2024-25** before easing to 33.6% in 2025-26.

| Year | Total US$ mn | Top market | Share | HHI |
|---|---|---|---|---|
| 2017-18 | 5,104 | China | 16.9% | 774 |
| 2018-19 | 5,625 | China | 22.7% | 922 |
| 2019-20 | 4,268 | Bangladesh | 15.5% | 701 |
| 2020-21 | 3,872 | Bangladesh | 18.4% | 843 |
| 2021-22 | 7,272 | Bangladesh | 31.3% | 1,297 |
| 2022-23 | 4,014 | Bangladesh | 25.5% | 967 |
| 2023-24 | 4,830 | Bangladesh | 28.2% | 1,195 |
| 2024-25 | 4,631 | Bangladesh | 37.7% | 1,604 |
| 2025-26 | 4,278 | Bangladesh | 33.6% | 1,414 |

India did not diversify away from Chinese demand. **It substituted one
dominant buyer for another**, and in cotton yarn the replacement is
more concentrated than the original.

The 2021-22 spike — US$ 7,272 million, 71% above the prior year,
followed by a 45% collapse — is post-pandemic restocking across global
textile supply chains and its correction. It is not a trend and should
not be read as one.

---

## Markets lost, and why

Eight destinations that once mattered now record effectively nothing:
**US$ 719.8 million of cumulative exports reduced to US$ 3.6 million
in the latest year.**

| Market | Cumulative | Latest year |
|---|---|---|
| **Pakistan** | **567.9** | — |
| Ukraine | 34.4 | 0.1 |
| Sudan | 28.6 | 0.1 |
| Uganda | 18.0 | 0.5 |
| Latvia | 17.3 | 0.8 |
| El Salvador | 14.9 | 0.9 |
| Austria | 14.2 | 0.3 |
| Montenegro | 14.0 | 0.8 |

**Pakistan alone accounts for 79% of the loss.** Exports ran at
US$ 260 million in 2017-18, fell to 205 the next year, then 52, then
zero — the bilateral trade suspension following August 2019.

Ukraine and Sudan are wars. The pattern is consistent: **these markets
were not lost to competitors on price or quality. They were closed by
events outside commercial control.**

That distinction matters for how an exporter should respond.
Competitive losses call for a pricing or service answer. Political
closures call for portfolio construction — which is precisely the
concentration question above.

---

## Where to push next

Classifying destinations on size against growth over the nine years:

**Core (large and growing)** — Bangladesh, Egypt, Peru, Vietnam.
Defend these. Bangladesh in particular warrants explicit exposure
management rather than simple account growth.

**Emerging (small and growing)** — Netherlands, Algeria, Romania,
Israel. The development list. None is large today; all are moving in
the right direction.

**Mature (large, flat or declining)** — China, Turkey, Brazil,
Portugal. Harvest and monitor. China's decline is the structural story
of the decade; Turkey remains the anchor for both synthetic headings.

**Marginal (small and declining)** — Myanmar, Argentina, Mauritius,
Tunisia. Deprioritise.

---

## What this suggests for an exporter

**1. Manage cotton yarn exposure to Bangladesh explicitly.**
At 43.3% of the heading and an HHI of 2,209, a duty change in Dhaka, a
taka devaluation, or a slump in Bangladeshi garment orders transmits
directly into Indian cotton spinning order books. The synthetic
headings demonstrate that a diversified destination mix is achievable
in yarn — cotton is the outlier, not the norm.

**2. Read concentration per heading, never on the chapter total.**
The aggregate index moved from "competitive" to "moderately
concentrated" and back within two years while the underlying cotton
trend rose steadily. Anyone monitoring the combined figure would have
missed it.

**3. Treat the Emerging quadrant as the development budget.**
Netherlands, Algeria, Romania and Israel are growing from small bases.
They will not replace Bangladesh, but four markets at 2-3% each
materially change the risk profile.

**4. Distinguish political loss from competitive loss when reviewing
lapsed accounts.** Seven of the eight lost markets closed for reasons
no commercial action would have prevented. Pursuing them as sales
failures wastes effort; treating them as concentration evidence does
not.

**5. Watch the 2025-26 easing carefully.** Bangladesh's share fell
from 37.7% to 33.6% and combined HHI from 1,604 to 1,414. One year is
not a trend, and the latest year is provisional. If it reverses, the
cotton trajectory resumes toward 2,500.

---

## Limitations

- **Three headings, not eleven.** 5205 (cotton yarn), 5402 (synthetic
  filament) and 5509 (synthetic staple) were selected as the highest-
  value yarn headings. Chapters 52, 54 and 55 also contain fibre,
  fabric and waste, which are excluded deliberately — chapter totals
  would overstate yarn exports substantially.
- **Latest year provisional.** DGCI&S revises recent figures; 2025-26
  should be treated as indicative.
- **HS codes were re-allocated from April 2026**, flagged by the
  source portal. Comparisons spanning that boundary need care.
- **Monthly analysis scoped out.** MEIDB provides national monthly
  totals without destination breakdown, so it could not be joined to
  the destination-level analysis that forms the core of this project.
  Seasonality is therefore not addressed.
- **No mirror data.** India's share of each destination's total yarn
  imports would require UN Comtrade reporter data, which is not
  included here. Without it, a declining Indian share and a declining
  market cannot be distinguished.
- **Values are FOB in US$ million** and unadjusted for inflation or
  exchange-rate movement.
- **2020-21 and 2021-22 were materially distorted** by the pandemic
  and the restocking cycle that followed.

---

## Method

Twenty-four files downloaded manually from Tradestat's EIDB
*Commodity wise all Countries* report — three headings across eight
financial years, each file returning the selected year and the prior
one. A Python pipeline reshapes the portal's wide layout into tidy
long format, deduplicates the two-year overlaps on
period-heading-destination, and maps DGCI&S country abbreviations
(`BANGLADESH PR`, `CHINA P RP`, `U ARAB EMTS`) to standard names for
mapping.

Analysis computes CAGR by destination, Herfindahl-Hirschman
concentration per heading and combined, a size-versus-growth
quadrant classification, and product mix by heading. Outputs render as
interactive HTML via plotly and as a four-page Power BI report built
on a conformed-dimension star schema.

Extraction and analysis code, plus the data collection guide, are in
the repository. The pipeline is reproducible end to end: drop the
downloads into `data/raw` and run `run_all.py`.

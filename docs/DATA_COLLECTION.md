# Data collection guide

Free and public. No login, no API. Budget about an hour.

---

## Which report to use

Tradestat offers eleven report types and the choice matters enormously:

| Report | Gives you | Downloads needed |
|---|---|---|
| Commodity x Country-wise | One HS code, **one country** | 11 x 200+ x 8 — unusable |
| **Commodity wise all Countries** | One HS code, **all countries**, one year | 11 x 8 = 88 |
| Chapter-wise all commodities | Chapter totals only, no destinations | — |

Use **Commodity wise all Countries**. The other country-level report makes
you pick a single destination per query, which would mean thousands of
downloads.

---

## 1. Annual data (EIDB)

**https://tradestat.commerce.gov.in/eidb/commodity_wise_all_countries_export**

Coverage: 2018-19 to 2025-26 (eight years in the dropdown).

The form has exactly three inputs:

1. **HS Code** — type the 4-digit heading, or use the *Search HSCode* box
2. **Year** — one financial year per query
3. **Values in** — choose **US $ Million**, not Rs Crore

Hit **Submit**, then export the result table.

### Naming your downloads — this part is not optional

The report returns one HS code for one year, so **neither the HS code nor
the year appears as a column in the file**. They exist only in the
filename. The parser reads them from there.

Save every file as `<hscode>_<year>.csv`:

```
5205_2018-19.csv
5205_2019-20.csv
5402_2018-19.csv
```

Get this wrong and the pipeline will reject the file with an error telling
you to rename it.

### Which headings

Do not use chapter totals. Chapters 52, 54 and 55 include raw fibre,
fabric and waste — chapter figures would be far larger than actual yarn
exports and the whole analysis would be wrong.

**Start with these three.** They carry most of the value, and 3 x 8 = 24
downloads is one sitting:

| Heading | What it is |
|---|---|
| **5205** | Cotton yarn, >=85% cotton, not retail |
| **5402** | Synthetic filament yarn, not retail |
| **5509** | Yarn of synthetic staple fibres, not retail |

**Add later for the complete picture:** 5206, 5207 (cotton), 5401, 5403,
5406 (filament), 5508, 5510, 5511 (staple).

Run the pipeline after the first three. If the output looks right, carry
on; if not, you have wasted 24 downloads rather than 88.

---

## 2. Monthly data (MEIDB) — for seasonality

**https://tradestat.commerce.gov.in/meidb/commoditywise_export**

Coverage: Jan 2018 to Mar 2026. Note this is **calendar** months, whereas
EIDB uses April-March financial years. Keep the two sets separate; the
pipeline already routes them to different analyses.

Same approach, same naming convention. Annual data cannot show seasonality,
and seasonality is one of the more commercially interesting findings here —
yarn shipments are not flat across the year.

---

## 3. Competitor benchmark (UN Comtrade)

Tradestat only knows what India ships. To answer "is India gaining or
losing share against China and Vietnam in the same headings", you need
mirror data:

```
py src\fetch_comtrade.py
```

The free public preview endpoint needs no authorisation. It is rate-limited,
so the script pauses between calls. If you hit limits, register a free key
at https://comtradedeveloper.un.org/ (auto-approved) and set it first:

```
set COMTRADE_KEY=your_key_here
```

---

## 4. Optional: port-wise data

Tradestat publishes port-wise trade under the FTSPCC section. Pulling it
makes the trade-lane map genuinely original — very few analyses look at
which Indian ports serve which destinations, and it is something you can
speak to from experience.

---

## Data quality notes

Things that will bite you:

- **Country names are DGCI&S abbreviations,** not standard names:
  `BANGLADESH PR`, `CHINA P RP`, `EGYPT A RP`, `KOREA RP`, `U ARAB EMTS`,
  `U K`, `U S A`, `VIETNAM SOC REP`, `SRI LANKA DSR`, `PAKISTAN IR`,
  `SAUDI ARAB`, `NETHERLAND`. The common ones are mapped in
  `visualise.NAME_FIXES`; add any others you meet.
- **`UNSPECIFIED` and `Trade to Unspecified Countries` are not
  destinations.** They are residual buckets and are dropped automatically.
- **Financial years run April-March.** `2023-24` = Apr 2023 to Mar 2024.
  Not directly comparable to Comtrade calendar years.
- **Nil is written as `-`,** not 0 or blank. Handled.
- **Total rows sit inside the table.** Dropped automatically, but sanity-
  check your row counts.
- **HS codes were re-allocated from April 2026** — the portal flags this.
  If a heading's value jumps oddly in the final year, that is likely why.
- **The latest year is provisional** and gets revised. Say so in your
  write-up; noting it shows you understand the source.

---

## Checklist

- [ ] 24 files (3 headings x 8 years) named `<hscode>_<year>.csv`
- [ ] All in US $ Million, not Rs Crore
- [ ] Saved to `data\raw\`
- [ ] `SYNTHETIC_*` files deleted
- [ ] `py src\run_all.py` runs without errors

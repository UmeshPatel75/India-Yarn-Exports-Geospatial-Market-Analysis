# India Yarn Exports — Geospatial Market Analysis

Where should an Indian yarn exporter be selling in 2026, and how exposed
is the trade to losing a single market?

Nine years of India's yarn export data (HS 52, 54, 55), analysed by
destination, product and season, mapped geospatially.

**Stack:** Python (pandas, plotly) · Power BI · public trade data

---

## Why this analysis

India exports several billion dollars of cotton and man-made yarn a year.
The destination mix is not stable — China's share of Indian cotton yarn
has moved sharply over the last decade, and the markets replacing it are
not the ones an exporter would have guessed in 2017.

Four questions, each with a commercial consequence:

1. **Where is the demand, and where is it moving?** Choropleth of value by
   destination across nine years.
2. **Which markets deserve investment?** Size-versus-growth quadrant
   separating Core, Emerging, Mature and Marginal destinations.
3. **How concentrated is the risk?** HHI over time, plus top-1 and top-5
   dependence. Concentration is the metric that tells you how badly a
   single trade-policy change could hurt.
4. **When does it ship?** Monthly seasonal index — working capital and
   booking decisions follow this.

---

## Quick start

```bash
pip install -r requirements.txt

# see the pipeline work on synthetic data first
python src/make_sample_data.py
python src/run_all.py
```

Then replace the synthetic files with real downloads:

```bash
rm data/raw/SYNTHETIC_*
# follow docs/DATA_COLLECTION.md, save downloads to data/raw/
python src/run_all.py
```

Outputs land in `output/` as standalone HTML (open in any browser) and in
`data/processed/analysis_tables.xlsx` for Power BI.

> **The bundled sample data is invented.** It exists so you can see the
> pipeline run before spending an evening on downloads. Delete it before
> publishing anything.

---

## Structure

```
├── data/raw/              Tradestat + Comtrade downloads go here
├── data/processed/        exports_long.csv, analysis_tables.xlsx
├── docs/DATA_COLLECTION.md   how to pull the data (start here)
├── output/                generated maps and charts
└── src/
    ├── config.py          HS codes, paths, port & country coordinates
    ├── ingest.py          Tradestat wide -> canonical long format
    ├── analysis.py        CAGR, HHI, quadrant, seasonality, product mix
    ├── visualise.py       choropleth, quadrant, concentration, flow map
    ├── fetch_comtrade.py  competitor benchmark via UN Comtrade API
    ├── make_sample_data.py  synthetic test fixtures
    └── run_all.py         orchestration
```

**Canonical data model.** Everything downstream reads one long table:

| period | hs_code | hs_desc | country | value_usd_mn |
|---|---|---|---|---|
| 2023-24 | 5205 | Cotton yarn ≥85% | Bangladesh | 612.40 |

Adding a new source means writing one parser that emits this shape.
Nothing else changes.

---

## Method notes

**Yarn, not chapters.** Chapters 52/54/55 contain fibre, fabric and waste
alongside yarn. The analysis filters to eleven 4-digit headings that are
specifically yarn. Chapter totals would have been easier and wrong.

**HHI on destination shares.** Runs 0–10,000; above 2,500 is conventionally
"highly concentrated". For an exporter this is a dependence measure, not a
competition measure.

**Seasonal index.** Each month is expressed against its own year's mean, then
averaged across years, so trend growth doesn't contaminate the seasonal
signal. 100 = an average month.

**Financial years.** Indian FY runs April–March, so `2023-24` is Apr 2023
to Mar 2024. Comtrade reports calendar years — the two are not directly
comparable and are kept in separate tables.

**Centroids are approximate.** The trade-lane map uses indicative country
centroids for drawing flows. Fine for showing lanes; not measurement data.

---

## Power BI layer

`data/processed/analysis_tables.xlsx` is built to load straight into Power
BI as a star schema: `fact_exports` plus the analysis tables as dimensions.
The intended report pages are Overview, Market Map, Growth & Risk, and
Seasonality.

---

## Sources

- **Tradestat / EIDB & MEIDB** — Directorate General of Commercial
  Intelligence and Statistics, Ministry of Commerce & Industry, Government
  of India. https://tradestat.commerce.gov.in/
- **UN Comtrade** — United Nations Statistics Division.
  https://comtradeplus.un.org/

Latest-year figures are provisional and subject to revision.

# Power BI build guide

Model: `data\processed\powerbi_model.xlsx`

Generate it with:

```
py src\build_powerbi_model.py
```

---

## Why two fact tables

The data has two grains. EIDB is annual (April-March financial years);
MEIDB is monthly. Putting both in one date table produces duplicate dates
— annual FY 2021-22 and monthly Apr-2021 both resolve to 1 April 2021 —
and Power BI will not accept a date table with duplicates.

So: `fact_annual` joins `dim_fy`, `fact_monthly` joins `dim_date`, and both
share `dim_country` and `dim_product`. This is a conformed-dimension star
schema and it is worth being able to explain in an interview.

```
        dim_fy                     dim_date
          |                            |
     fact_annual                 fact_monthly
          |    \                  /    |
          |     dim_country ------     |
          |            |               |
          ------- dim_product ----------
```

---

## 1. Load

**Home → Get Data → Excel workbook** → select `powerbi_model.xlsx`.

Tick all six sheets: `fact_annual`, `fact_monthly`, `dim_fy`, `dim_date`,
`dim_country`, `dim_product`. Click **Transform Data**, not Load.

In Power Query, confirm data types:

| Table | Column | Type |
|---|---|---|
| fact_annual | value_usd_mn | Decimal Number |
| fact_monthly | value_usd_mn | Decimal Number |
| dim_date | date | Date |
| dim_fy | fy_start_date | Date |
| dim_country | latitude, longitude | Decimal Number |

Then **Close & Apply**.

---

## 2. Relationships

Model view. Create these six, all **one-to-many**, single direction, from
dimension to fact:

| From | To |
|---|---|
| dim_fy[fy_label] | fact_annual[fy_label] |
| dim_country[country_key] | fact_annual[country_key] |
| dim_product[hs_heading] | fact_annual[hs_heading] |
| dim_date[year_month] | fact_monthly[year_month] |
| dim_country[country_key] | fact_monthly[country_key] |
| dim_product[hs_heading] | fact_monthly[hs_heading] |

Delete any relationship Power BI auto-created that is not on this list.

**Mark the date table:** select `dim_date` → **Table tools → Mark as date
table** → date column = `date`. Time intelligence will not work otherwise.

**Set sort columns** (otherwise months sort alphabetically):

- `dim_date[month_name]` → Sort by → `month_sort` (Apr = 1, matching FY)
- `dim_date[month_short]` → Sort by → `month_sort`
- `dim_fy[fy_label]` → Sort by → `sort_order`

---

## 3. Measures

Create a blank table called `_Measures` (Home → Enter Data → name it
`_Measures` → Load), then put every measure there. Keeps them out of the
fact tables and visible at the top of the field list.

### Base

```dax
Total Exports = SUM(fact_annual[value_usd_mn])
```

```dax
Exports PY =
VAR CurrentFY = SELECTEDVALUE(dim_fy[fy_start_year])
RETURN
CALCULATE(
    [Total Exports],
    REMOVEFILTERS(dim_fy),
    dim_fy[fy_start_year] = CurrentFY - 1
)
```

```dax
YoY Growth % = DIVIDE([Total Exports] - [Exports PY], [Exports PY])
```

```dax
Latest FY Value =
VAR LastFY = CALCULATE(MAX(dim_fy[fy_start_year]), REMOVEFILTERS(dim_fy))
RETURN
CALCULATE(
    [Total Exports],
    REMOVEFILTERS(dim_fy),
    dim_fy[fy_start_year] = LastFY
)
```

### Growth

```dax
CAGR % =
VAR FirstFY = CALCULATE(MIN(dim_fy[fy_start_year]), REMOVEFILTERS(dim_fy))
VAR LastFY  = CALCULATE(MAX(dim_fy[fy_start_year]), REMOVEFILTERS(dim_fy))
VAR V1 = CALCULATE([Total Exports], REMOVEFILTERS(dim_fy),
                   dim_fy[fy_start_year] = FirstFY)
VAR V2 = CALCULATE([Total Exports], REMOVEFILTERS(dim_fy),
                   dim_fy[fy_start_year] = LastFY)
VAR Years = LastFY - FirstFY
RETURN
IF(V1 > 0 && Years > 0, (V2 / V1) ^ DIVIDE(1, Years) - 1)
```

### Share and rank

```dax
Market Share % =
DIVIDE([Total Exports], CALCULATE([Total Exports], REMOVEFILTERS(dim_country)))
```

```dax
Market Rank =
RANKX(ALL(dim_country[country_clean]), [Total Exports], , DESC, Dense)
```

```dax
Active Markets =
CALCULATE(
    DISTINCTCOUNT(fact_annual[country_key]),
    fact_annual[value_usd_mn] > 0
)
```

### Concentration risk

This is the measure worth showing off. It reproduces the Herfindahl-
Hirschman Index in DAX by iterating destinations and squaring each share.

```dax
HHI =
VAR TotalAll = CALCULATE([Total Exports], ALLSELECTED(dim_country))
RETURN
SUMX(
    ALLSELECTED(dim_country[country_clean]),
    VAR CountryValue = CALCULATE([Total Exports])
    RETURN DIVIDE(CountryValue, TotalAll) ^ 2 * 10000
)
```

```dax
Top 5 Share % =
VAR TotalAll = CALCULATE([Total Exports], ALLSELECTED(dim_country))
VAR Top5 =
    TOPN(5, ALLSELECTED(dim_country[country_clean]),
         CALCULATE([Total Exports]), DESC)
RETURN
DIVIDE(SUMX(Top5, CALCULATE([Total Exports])), TotalAll)
```

```dax
Concentration Status =
VAR H = [HHI]
RETURN
SWITCH(
    TRUE(),
    H >= 2500, "Highly concentrated",
    H >= 1500, "Moderately concentrated",
    "Competitive"
)
```

### Market quadrant

```dax
Median Market Size =
MEDIANX(ALLSELECTED(dim_country[country_clean]), [Latest FY Value])
```

```dax
Market Quadrant =
VAR Sz  = [Latest FY Value]
VAR G   = [CAGR %]
VAR Med = CALCULATE([Median Market Size], REMOVEFILTERS(dim_country))
RETURN
SWITCH(
    TRUE(),
    ISBLANK(G) || Sz = 0,      "Not classified",
    Sz >= Med && G > 0,        "Core",
    Sz <  Med && G > 0,        "Emerging",
    Sz >= Med && G <= 0,       "Mature",
                               "Marginal"
)
```

### Seasonality

```dax
Monthly Exports = SUM(fact_monthly[value_usd_mn])
```

```dax
Seasonal Index =
VAR AvgThisMonth = AVERAGEX(VALUES(dim_date[date]), [Monthly Exports])
VAR AvgAllMonths =
    CALCULATE(
        AVERAGEX(VALUES(dim_date[date]), [Monthly Exports]),
        REMOVEFILTERS(dim_date[month_no], dim_date[month_name],
                      dim_date[month_short], dim_date[month_sort])
    )
RETURN
DIVIDE(AvgThisMonth, AvgAllMonths) * 100
```

100 = an average month. Each month is measured against the overall mean,
so trend growth does not contaminate the seasonal signal.

### Formatting

Set these in Measure tools as you create each one:

- `Total Exports`, `Exports PY`, `Latest FY Value` — Decimal, 1 dp
- `YoY Growth %`, `CAGR %`, `Market Share %`, `Top 5 Share %` — Percentage, 1 dp
- `HHI`, `Seasonal Index` — Whole number
- `Active Markets`, `Market Rank` — Whole number

---

## 4. Report pages

Four pages. Keep one message per page.

### Page 1 — Overview

- **Cards** (top row): `Total Exports`, `YoY Growth %`, `Active Markets`,
  `CAGR %`
- **Line chart**: axis `dim_fy[fy_label]`, value `Total Exports`
- **Stacked column**: axis `dim_fy[fy_label]`, legend
  `dim_product[fibre_type]`, value `Total Exports` — shows the cotton
  versus man-made shift
- **Bar chart**: axis `dim_country[country_clean]`, value `Total Exports`,
  Top-10 filter
- **Slicers**: `dim_fy[fy_label]`, `dim_product[chapter_desc]`,
  `dim_country[region]`

### Page 2 — Market Map

- **Map visual** (Azure Map or filled Map): location
  `dim_country[country_clean]`, size `Total Exports`, tooltips
  `Market Share %`, `CAGR %`, `Market Rank`
- **Matrix**: rows `dim_country[region]` then `country_clean`; values
  `Total Exports`, `Market Share %`, `YoY Growth %`
- **Play axis / slicer** on `dim_fy[fy_label]` to animate across years

If the map leaves countries blank, use `latitude` / `longitude` from
`dim_country` instead of name matching.

### Page 3 — Growth & Risk

- **Scatter chart**: X `Latest FY Value` (log scale), Y `CAGR %`, legend
  `Market Quadrant`, details `dim_country[country_clean]`, size
  `Total Exports`
- **Cards**: `HHI`, `Concentration Status`, `Top 5 Share %`
- **Line chart**: axis `dim_fy[fy_label]`, value `HHI` — add a constant
  line at 2500 (Analytics pane) labelled "Highly concentrated"
- **Two tables**: top gainers and top losers, sorted by `YoY Growth %`

### Page 4 — Seasonality

- **Column chart**: axis `dim_date[month_short]`, value `Seasonal Index`,
  constant line at 100
- **Line chart**: axis `dim_date[date]`, value `Monthly Exports` — the raw
  monthly series
- **Matrix**: rows `dim_date[fy_label]`, columns `dim_date[month_short]`,
  values `Monthly Exports`, conditional formatting as a heat map
- **Slicers**: `dim_product[fibre_type]`, `dim_country[region]`

---

## 5. Polish

- Consistent theme: View → Themes → Customise. Navy `#1F3864` as primary,
  red `#C00000` for warnings, keeps it consistent with the Python charts.
- Every visual gets a title stating the finding, not the mechanics.
  "Bangladesh now takes a third of India's yarn exports" beats "Sum of
  value by country".
- Add a text box on Page 1: data source, period covered, and the note that
  the latest year is provisional.
- Hide from report view: all key columns (`country_key`, `hs_heading`,
  `year_month`, `fy_label` in facts), `sort_order`, `month_sort`.
- Bookmarks are worth adding if you want to demo cotton-versus-synthetic
  toggling in an interview.

---

## Common problems

**Map shows nothing** — country names are not matching Bing's list. Use
lat/long fields, and set `country_clean` Data category to Country/Region.

**Time intelligence returns blank** — `dim_date` is not marked as a date
table, or has gaps. The builder generates a contiguous range, so re-run it
if you edited the sheet.

**Months sort A-Z** — sort column not set on `month_name` / `month_short`.

**Values look far too large** — you probably downloaded in Rs Crore for
some files and US $ Million for others. Check `data\raw\` and re-download
the odd ones.

**Blank rows in `dim_country`** — a DGCI&S spelling not yet in
`NAME_FIXES`. Add it in `visualise.py` and re-run the builder.

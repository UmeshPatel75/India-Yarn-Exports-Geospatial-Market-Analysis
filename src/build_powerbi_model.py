"""Export a proper star schema for Power BI.

analysis_tables.xlsx holds *results*. Power BI wants *dimensions* -- tables
it can slice by. This builds:

    fact_exports    one row per period x country x product
    dim_date        period, FY, month, real date column for time intelligence
    dim_country     destination, cleaned name, region, lat/lon for maps
    dim_product     HS heading, chapter, fibre type

    python src/build_powerbi_model.py
"""
from __future__ import annotations

import pandas as pd

import ingest
from config import PROCESSED, COUNTRY_CENTROIDS, YARN_HEADINGS
from visualise import _clean_names

# --- region lookup -------------------------------------------------------
REGIONS = {
    "South Asia": ["Bangladesh", "Sri Lanka", "Nepal", "Pakistan", "Bhutan",
                   "Maldives", "Afghanistan"],
    "East & SE Asia": ["China", "Vietnam", "South Korea", "Japan", "Taiwan",
                       "Hong Kong", "Indonesia", "Thailand", "Malaysia",
                       "Singapore", "Philippines", "Cambodia", "Myanmar",
                       "Laos", "North Korea", "Macao", "Mongolia", "Brunei"],
    "Middle East": ["United Arab Emirates", "Saudi Arabia", "Iran", "Iraq",
                    "Oman", "Qatar", "Kuwait", "Bahrain", "Jordan", "Yemen",
                    "Israel", "Lebanon", "Syria", "Palestine"],
    "Europe": ["Turkey", "Italy", "Germany", "Spain", "Portugal", "France",
               "United Kingdom", "Belgium", "Netherlands", "Poland", "Russia",
               "Ukraine", "Czechia", "Greece", "Romania", "Bulgaria",
               "Switzerland", "Austria", "Sweden", "Denmark", "Norway",
               "Finland", "Ireland", "Hungary", "Slovakia", "Slovenia",
               "Croatia", "Serbia", "Lithuania", "Latvia", "Estonia",
               "Belarus", "North Macedonia", "Albania", "Bosnia and Herzegovina"],
    "Africa": ["Egypt", "Morocco", "Tunisia", "Algeria", "Nigeria", "Kenya",
               "Ethiopia", "South Africa", "Tanzania", "Ghana", "Uganda",
               "Sudan", "Libya", "Mauritius", "Madagascar", "Senegal",
               "Ivory Coast", "Zimbabwe", "Zambia", "Mozambique"],
    "Americas": ["United States", "Brazil", "Peru", "Colombia", "Mexico",
                 "Argentina", "Chile", "Canada", "Guatemala", "Honduras",
                 "Ecuador", "Uruguay", "Venezuela", "Dominican Republic",
                 "Costa Rica", "Panama", "El Salvador", "Bolivia", "Paraguay"],
    "Oceania & CIS": ["Australia", "New Zealand", "Uzbekistan", "Kazakhstan",
                      "Turkmenistan", "Kyrgyzstan", "Tajikistan", "Azerbaijan",
                      "Georgia", "Armenia", "Fiji"],
}
COUNTRY_TO_REGION = {c: r for r, cs in REGIONS.items() for c in cs}

FIBRE_TYPE = {
    "5205": "Cotton", "5206": "Cotton", "5207": "Cotton",
    "5401": "Man-made filament", "5402": "Man-made filament",
    "5403": "Artificial filament", "5406": "Man-made filament",
    "5508": "Man-made staple", "5509": "Synthetic staple",
    "5510": "Artificial staple", "5511": "Man-made staple",
}
CHAPTER_DESC = {"52": "Cotton", "54": "Man-made filaments",
                "55": "Man-made staple fibres"}
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]


def build_dim_country(countries: pd.Series) -> pd.DataFrame:
    raw = sorted(set(countries.astype(str)))
    clean = _clean_names(pd.Series(raw))
    df = pd.DataFrame({"country_key": raw, "country_clean": clean.values})
    df = df[df["country_clean"].notna()]
    df["region"] = df["country_clean"].map(COUNTRY_TO_REGION).fillna("Other")
    df["latitude"] = df["country_clean"].map(
        lambda c: COUNTRY_CENTROIDS.get(c, (None, None))[0])
    df["longitude"] = df["country_clean"].map(
        lambda c: COUNTRY_CENTROIDS.get(c, (None, None))[1])
    return df.reset_index(drop=True)


def build_dim_product(hs_codes: pd.Series) -> pd.DataFrame:
    heads = sorted({str(h)[:4] for h in hs_codes if str(h)[:4] in YARN_HEADINGS})
    df = pd.DataFrame({"hs_heading": heads})
    df["heading_desc"] = df["hs_heading"].map(YARN_HEADINGS)
    df["chapter"] = df["hs_heading"].str[:2]
    df["chapter_desc"] = df["chapter"].map(CHAPTER_DESC)
    df["fibre_type"] = df["hs_heading"].map(FIBRE_TYPE)
    df["retail"] = df["hs_heading"].isin(["5207", "5406", "5511"])
    return df



def build_dim_fy(periods) -> pd.DataFrame:
    """Annual grain: one row per Indian financial year."""
    fys = sorted({str(p) for p in periods})
    rows = []
    for p in fys:
        start = int(p[:4])
        rows.append({
            "fy_label": p,
            "fy_start_year": start,
            "fy_end_year": start + 1,
            "fy_start_date": pd.Timestamp(year=start, month=4, day=1),
            "sort_order": start,
        })
    df = pd.DataFrame(rows)
    df["is_latest"] = df["fy_start_year"] == df["fy_start_year"].max()
    return df


def build_dim_date(periods) -> pd.DataFrame:
    """Monthly grain: a contiguous, gap-free date table.

    Power BI's time intelligence requires unique, continuous dates. Built
    from the full span of the data rather than only the months present, so
    a missing month does not break the table.
    """
    months = sorted({str(p) for p in periods})
    if not months:
        return pd.DataFrame()
    lo = pd.Timestamp(f"{months[0]}-01")
    hi = pd.Timestamp(f"{months[-1]}-01") + pd.offsets.MonthBegin(1)
    rng = pd.date_range(lo, hi, freq="MS", inclusive="left")

    df = pd.DataFrame({"date": rng})
    df["year_month"] = df["date"].dt.strftime("%Y-%m")
    df["calendar_year"] = df["date"].dt.year
    df["month_no"] = df["date"].dt.month
    df["month_name"] = df["month_no"].map(lambda m: MONTH_NAMES[m - 1])
    df["month_short"] = df["month_name"].str[:3]
    # Indian FY: Jan-Mar belong to the FY that began the previous April
    fy_start = df["calendar_year"].where(df["month_no"] > 3,
                                         df["calendar_year"] - 1)
    df["fy_label"] = fy_start.astype(str) + "-" + \
        (fy_start + 1).astype(str).str[2:]
    df["fy_quarter"] = ((df["month_no"] - 4) % 12) // 3 + 1
    df["month_sort"] = ((df["month_no"] - 4) % 12) + 1   # Apr=1 ... Mar=12
    return df


def main() -> None:
    src = PROCESSED / "exports_long.csv"
    if not src.exists():
        raise FileNotFoundError("Run src/ingest.py first.")
    df = pd.read_csv(src)
    df["hs_heading"] = df["hs_code"].astype(str).str[:4]
    df = df.rename(columns={"country": "country_key"})

    is_monthly = df["period"].astype(str).str.match(r"^\d{4}-(0[1-9]|1[0-2])$")

    annual = (df[~is_monthly]
              .groupby(["period", "country_key", "hs_heading"], as_index=False)
              ["value_usd_mn"].sum()
              .rename(columns={"period": "fy_label"}))
    monthly = (df[is_monthly]
               .groupby(["period", "country_key", "hs_heading"], as_index=False)
               ["value_usd_mn"].sum()
               .rename(columns={"period": "year_month"}))

    dim_country = build_dim_country(
        pd.concat([annual["country_key"], monthly["country_key"]]))
    dim_product = build_dim_product(
        pd.concat([annual["hs_heading"], monthly["hs_heading"]]))
    dim_fy = build_dim_fy(annual["fy_label"])
    dim_date = build_dim_date(monthly["year_month"])

    keep = dim_country["country_key"]
    annual = annual[annual["country_key"].isin(keep)]
    monthly = monthly[monthly["country_key"].isin(keep)]

    out = PROCESSED / "powerbi_model.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        annual.to_excel(w, sheet_name="fact_annual", index=False)
        # Always write these two sheets, even when empty. Power BI holds a
        # query per sheet; omitting a sheet breaks refresh with
        # "the key didn't match any rows in the table".
        if monthly.empty:
            monthly = pd.DataFrame(columns=["year_month", "country_key",
                                            "hs_heading", "value_usd_mn"])
        if dim_date.empty:
            dim_date = pd.DataFrame(columns=[
                "date", "year_month", "calendar_year", "month_no",
                "month_name", "month_short", "fy_label", "fy_quarter",
                "month_sort"])
        monthly.to_excel(w, sheet_name="fact_monthly", index=False)
        dim_date.to_excel(w, sheet_name="dim_date", index=False)
        dim_fy.to_excel(w, sheet_name="dim_fy", index=False)
        dim_country.to_excel(w, sheet_name="dim_country", index=False)
        dim_product.to_excel(w, sheet_name="dim_product", index=False)

    print(f"fact_annual   {len(annual):>6,} rows")
    print(f"fact_monthly  {len(monthly):>6,} rows")
    print(f"dim_fy        {len(dim_fy):>6,} rows")
    print(f"dim_date      {len(dim_date):>6,} rows "
          f"(unique dates: {dim_date['date'].nunique() if len(dim_date) else 0})")
    print(f"dim_country   {len(dim_country):>6,} rows "
          f"({dim_country['latitude'].isna().sum()} missing coordinates)")
    print(f"dim_product   {len(dim_product):>6,} rows")
    print(f"\n-> {out}")

    missing = dim_country[dim_country["latitude"].isna()]["country_clean"].tolist()
    if missing:
        print(f"\nNo coordinates for: {', '.join(missing[:15])}")
        print("Add them to COUNTRY_CENTROIDS in config.py to map them.")


if __name__ == "__main__":
    main()

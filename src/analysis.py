"""Analytical layer: the questions an exporter actually asks.

Every function takes the canonical long dataframe and returns a tidy
result you can inspect, export to Excel, or feed into Power BI.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# --- helpers -------------------------------------------------------------

def _fy_start(period: str) -> int:
    """'2023-24' -> 2023 ; '2023' -> 2023 ; '2024-04' -> 2024."""
    return int(str(period)[:4])


def annual_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse to one row per country per period."""
    out = (df.groupby(["period", "country"], as_index=False)["value_usd_mn"]
             .sum())
    out["year"] = out["period"].map(_fy_start)
    return out


# --- 1. Growth ------------------------------------------------------------

def cagr(df: pd.DataFrame, min_value: float = 1.0) -> pd.DataFrame:
    """Compound annual growth rate per destination, first period to last.

    min_value filters out micro-markets whose growth rates are noise.
    """
    a = annual_by_country(df)
    first_p, last_p = a["period"].min(), a["period"].max()
    span = _fy_start(last_p) - _fy_start(first_p)
    if span <= 0:
        raise ValueError("Need at least two periods to compute CAGR.")

    wide = (a.pivot_table(index="country", columns="period",
                          values="value_usd_mn", aggfunc="sum")
              .fillna(0.0))
    res = pd.DataFrame({
        "country": wide.index,
        "value_first": wide[first_p].values,
        "value_last": wide[last_p].values,
    })
    res["total_period"] = wide.sum(axis=1).values
    res = res[res["value_last"] >= min_value]

    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = res["value_last"] / res["value_first"].replace(0, np.nan)
        res["cagr_pct"] = (ratio ** (1 / span) - 1) * 100

    res["abs_change"] = res["value_last"] - res["value_first"]
    res["share_last_pct"] = res["value_last"] / res["value_last"].sum() * 100
    return (res.sort_values("value_last", ascending=False)
               .reset_index(drop=True))


# --- 2. Concentration risk ------------------------------------------------

def hhi(df: pd.DataFrame) -> pd.DataFrame:
    """Herfindahl-Hirschman Index of destination concentration, per period.

    Computed on percentage shares, so it runs 0-10,000. Above 2,500 is
    conventionally 'highly concentrated' -- for an exporter that means
    dangerous dependence on a handful of buyers' markets.
    """
    a = annual_by_country(df)
    rows = []
    for period, grp in a.groupby("period"):
        total = grp["value_usd_mn"].sum()
        if total <= 0:
            continue
        shares = grp["value_usd_mn"] / total * 100
        ranked = grp.assign(share=shares).nlargest(5, "value_usd_mn")
        rows.append({
            "period": period,
            "total_usd_mn": total,
            "n_markets": int((grp["value_usd_mn"] > 0).sum()),
            "hhi": float((shares ** 2).sum()),
            "top1_share_pct": float(shares.max()),
            "top5_share_pct": float(ranked["share"].sum()),
            "top1_market": grp.loc[grp["value_usd_mn"].idxmax(), "country"],
        })
    out = pd.DataFrame(rows).sort_values("period").reset_index(drop=True)
    out["concentration"] = pd.cut(
        out["hhi"], bins=[-1, 1500, 2500, 10001],
        labels=["Competitive", "Moderately concentrated", "Highly concentrated"])
    return out


# --- 3. Market attractiveness quadrant ------------------------------------

def market_quadrant(df: pd.DataFrame, min_value: float = 5.0) -> pd.DataFrame:
    """Classify destinations on size (latest value) vs growth (CAGR).

    The four boxes map to real commercial decisions:
      Core        -- big and growing: defend, invest in service
      Emerging    -- small but growing fast: where to open next
      Mature      -- big but flat/declining: harvest, watch for erosion
      Marginal    -- small and shrinking: deprioritise
    """
    g = cagr(df, min_value=min_value)
    g = g[g["cagr_pct"].notna()].copy()
    size_cut = g["value_last"].median()
    growth_cut = 0.0  # real growth vs contraction

    def label(r):
        big = r["value_last"] >= size_cut
        growing = r["cagr_pct"] > growth_cut
        if big and growing:
            return "Core"
        if not big and growing:
            return "Emerging"
        if big and not growing:
            return "Mature"
        return "Marginal"

    g["quadrant"] = g.apply(label, axis=1)
    g["size_threshold"] = size_cut
    return g.sort_values(["quadrant", "value_last"],
                         ascending=[True, False]).reset_index(drop=True)


# --- 4. Seasonality (needs MEIDB monthly data) ----------------------------

def seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly seasonal index. 100 = an average month.

    Only meaningful on MEIDB monthly downloads, where period is 'YYYY-MM'.
    """
    monthly = df[df["period"].astype(str).str.match(r"^\d{4}-\d{2}$")].copy()
    if monthly.empty:
        raise ValueError(
            "No monthly periods found. Download MEIDB data for seasonality.")

    monthly["month"] = monthly["period"].str[-2:].astype(int)
    monthly["year"] = monthly["period"].str[:4].astype(int)

    by_month = (monthly.groupby(["year", "month"], as_index=False)["value_usd_mn"]
                       .sum())
    yearly_mean = by_month.groupby("year")["value_usd_mn"].transform("mean")
    by_month["index"] = by_month["value_usd_mn"] / yearly_mean * 100

    out = (by_month.groupby("month", as_index=False)
                   .agg(seasonal_index=("index", "mean"),
                        std_dev=("index", "std"),
                        n_years=("index", "size")))
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out["month_name"] = out["month"].map(lambda m: names[m - 1])
    return out


# --- 5. Product mix -------------------------------------------------------

def product_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Value and share by yarn heading, per period.

    Requires filter_yarn() to have been applied so 'heading' exists.
    """
    if "heading" not in df.columns:
        raise ValueError("Run ingest.filter_yarn(df) first.")
    out = (df.groupby(["period", "heading", "heading_desc", "chapter"],
                      as_index=False)["value_usd_mn"].sum())
    out["share_pct"] = (out["value_usd_mn"] /
                        out.groupby("period")["value_usd_mn"].transform("sum") * 100)
    return out.sort_values(["period", "value_usd_mn"], ascending=[True, False])


# --- 6. Movers ------------------------------------------------------------

def biggest_movers(df: pd.DataFrame, n: int = 10) -> dict[str, pd.DataFrame]:
    """Largest absolute gains and losses between first and last period."""
    g = cagr(df, min_value=0.5)
    cols = ["country", "value_first", "value_last", "abs_change", "cagr_pct"]
    return {
        "gainers": g.nlargest(n, "abs_change")[cols].reset_index(drop=True),
        "losers": g.nsmallest(n, "abs_change")[cols].reset_index(drop=True),
    }

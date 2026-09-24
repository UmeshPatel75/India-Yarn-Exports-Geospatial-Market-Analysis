"""Run the whole pipeline: ingest -> analyse -> chart -> Excel export.

    python src/run_all.py
"""
from __future__ import annotations

import pandas as pd

import analysis as an
import ingest
import visualise as viz
from config import PROCESSED, OUTPUT


def main() -> None:
    print("1. Ingesting raw downloads")
    df = ingest.build()

    # Annual rows carry an HS code; monthly MEIDB rows usually do not.
    is_monthly = df["period"].astype(str).str.match(r"^\d{4}-(0[1-9]|1[0-2])$")
    annual = df[~is_monthly].copy()
    monthly = df[is_monthly].copy()
    print(f"   annual rows: {len(annual):,}   monthly rows: {len(monthly):,}")

    yarn = ingest.filter_yarn(annual)
    base = yarn if not yarn.empty else annual
    if yarn.empty:
        print("   ! No yarn HS headings matched -- using all annual rows.")
    else:
        print(f"   yarn-only rows: {len(yarn):,} "
              f"({yarn['heading'].nunique()} headings)")

    print("\n2. Analysing")
    growth = an.cagr(base)
    conc = an.hhi(base)
    quad = an.market_quadrant(base)
    movers = an.biggest_movers(base)
    sheets = {
        "market_growth": growth,
        "concentration": conc,
        "quadrant": quad,
        "top_gainers": movers["gainers"],
        "top_losers": movers["losers"],
    }
    if not yarn.empty:
        sheets["product_mix"] = an.product_mix(yarn)
    if not monthly.empty:
        sheets["seasonality"] = an.seasonality(monthly)

    for name, tbl in sheets.items():
        print(f"   {name:<18} {len(tbl):>5} rows")

    xl = PROCESSED / "analysis_tables.xlsx"
    with pd.ExcelWriter(xl, engine="openpyxl") as writer:
        for name, tbl in sheets.items():
            tbl.to_excel(writer, sheet_name=name[:31], index=False)
        base.to_excel(writer, sheet_name="fact_exports", index=False)
    print(f"   -> {xl}")

    print("\n3. Building charts")
    made = [viz.choropleth(base), viz.quadrant(base),
            viz.concentration(base), viz.trade_lanes(base)]
    if not monthly.empty:
        made.append(viz.seasonality_chart(monthly))
    for p in made:
        print(f"   -> {p}")

    print("\n4. Headline findings")
    latest = conc.iloc[-1]
    print(f"   Latest period {latest['period']}: "
          f"US$ {latest['total_usd_mn']:,.0f} mn across "
          f"{latest['n_markets']} markets")
    print(f"   HHI {latest['hhi']:,.0f} ({latest['concentration']}); "
          f"top market {latest['top1_market']} at "
          f"{latest['top1_share_pct']:.1f}%, top 5 at "
          f"{latest['top5_share_pct']:.1f}%")
    for q in ["Core", "Emerging", "Mature", "Marginal"]:
        names = quad[quad["quadrant"] == q]["country"].head(4).tolist()
        print(f"   {q:<9}: {', '.join(names) if names else '-'}")

    print("\nDone. Open the HTML files in output/.")


if __name__ == "__main__":
    main()

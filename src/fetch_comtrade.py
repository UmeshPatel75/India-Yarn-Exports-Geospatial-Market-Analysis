"""Pull competitor benchmark data from UN Comtrade.

Tradestat tells you what India exports. It cannot tell you whether India
is gaining or losing share against China, Vietnam, Turkey and Pakistan in
the same yarn headings. Comtrade can.

The free public preview endpoint needs no key:
    https://comtradeapi.un.org/public/v1/preview/C/A/HS

It is rate-limited and caps rows per call, so this script loops one
reporter-year at a time and caches to disk. For heavier pulls, register a
free key at https://comtradedeveloper.un.org/ and set COMTRADE_KEY.

    python src/fetch_comtrade.py
"""
from __future__ import annotations

import os
import time

import pandas as pd
import requests

from config import RAW

BASE = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
KEY = os.environ.get("COMTRADE_KEY")

# UN M49 numeric reporter codes
REPORTERS = {
    699: "India", 156: "China", 704: "Viet Nam",
    792: "Turkiye", 586: "Pakistan", 360: "Indonesia",
}
YARN_HEADINGS = ["5205", "5206", "5207", "5402", "5509", "5510", "5511"]
YEARS = list(range(2018, 2026))


def fetch(reporter: int, year: int) -> pd.DataFrame:
    params = {
        "reporterCode": reporter,
        "period": year,
        "flowCode": "X",              # exports
        "cmdCode": ",".join(YARN_HEADINGS),
        "partnerCode": None,          # all partners
        "includeDesc": "true",
    }
    if KEY:
        params["subscription-key"] = KEY

    r = requests.get(BASE, params={k: v for k, v in params.items()
                                   if v is not None}, timeout=60)
    r.raise_for_status()
    payload = r.json()
    rows = payload.get("data") or []
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    keep = {
        "refYear": "year", "reporterDesc": "reporter",
        "partnerDesc": "partner", "cmdCode": "hs_code",
        "cmdDesc": "hs_desc", "primaryValue": "value_usd",
        "netWgt": "net_weight_kg",
    }
    df = df[[c for c in keep if c in df.columns]].rename(columns=keep)
    return df


def main() -> None:
    out_path = RAW / "comtrade_yarn_competitors.csv"
    frames = []
    for code, name in REPORTERS.items():
        for year in YEARS:
            try:
                d = fetch(code, year)
                if not d.empty:
                    frames.append(d)
                    print(f"  {name} {year}: {len(d):,} rows")
                else:
                    print(f"  {name} {year}: no data")
            except requests.HTTPError as e:
                print(f"  {name} {year}: HTTP {e.response.status_code} "
                      f"(rate limit? wait and retry)")
            except Exception as e:
                print(f"  {name} {year}: {e}")
            time.sleep(2)   # be polite to a free public endpoint

    if not frames:
        print("\nNothing fetched. Check your connection, or register a free "
              "key at https://comtradedeveloper.un.org/ and set COMTRADE_KEY.")
        return

    df = pd.concat(frames, ignore_index=True)
    df.to_csv(out_path, index=False)
    print(f"\n{len(df):,} rows -> {out_path}")

    share = (df.groupby(["year", "reporter"], as_index=False)["value_usd"].sum())
    share["share_pct"] = (share["value_usd"] /
                          share.groupby("year")["value_usd"].transform("sum") * 100)
    print("\nShare of the six-country yarn export total:")
    print(share.pivot(index="year", columns="reporter", values="share_pct")
               .round(1).to_string())


if __name__ == "__main__":
    main()

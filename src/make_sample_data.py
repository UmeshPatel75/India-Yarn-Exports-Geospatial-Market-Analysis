"""Generate SYNTHETIC Tradestat-shaped files so the pipeline can be tested
before the real downloads arrive.

The numbers are invented. They are plausible in shape -- Bangladesh large,
a COVID dip in 2020-21, a Q3 seasonal peak -- but they are NOT real trade
figures and must never appear in a published portfolio. Delete data/raw/
and re-run ingest once you have the genuine downloads.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import RAW, YARN_HEADINGS

rng = np.random.default_rng(42)

FY = ["2017-18", "2018-19", "2019-20", "2020-21", "2021-22",
      "2022-23", "2023-24", "2024-25"]

# country -> (base value US$ mn, annual drift, volatility)
MARKETS = {
    "BANGLADESH PR": (610, 0.09, 0.10), "CHINA P RP": (540, -0.14, 0.28),
    "VIETNAM SOC REP": (150, 0.13, 0.14), "TURKEY": (120, 0.05, 0.16),
    "EGYPT A RP": (95, 0.07, 0.13), "PERU": (85, 0.03, 0.12),
    "KOREA RP": (78, -0.02, 0.11), "PORTUGAL": (70, 0.06, 0.12),
    "ITALY": (66, 0.01, 0.11), "SRI LANKA DSR": (58, 0.04, 0.15),
    "U S A": (54, 0.08, 0.13), "COLOMBIA": (46, 0.02, 0.14),
    "BRAZIL": (42, 0.06, 0.17), "GERMANY": (38, -0.01, 0.10),
    "SPAIN": (34, 0.03, 0.12), "INDONESIA": (31, 0.10, 0.16),
    "NEPAL": (28, 0.12, 0.18), "MOROCCO": (24, 0.09, 0.14),
    "U ARAB EMTS": (22, -0.05, 0.19), "THAILAND": (20, 0.04, 0.13),
    "MEXICO": (18, 0.07, 0.15), "JAPAN": (16, -0.03, 0.11),
    "MALAYSIA": (14, 0.02, 0.14), "PAKISTAN IR": (12, -0.09, 0.30),
    "ETHIOPIA": (9, 0.15, 0.22), "TUNISIA": (8, 0.04, 0.15),
    "POLAND": (7, 0.08, 0.16), "U K": (6, 0.01, 0.13),
    "ARGENTINA": (5, 0.03, 0.20), "KENYA": (4, 0.14, 0.24),
}

# Chapter shares of the yarn basket, roughly
HEADING_WEIGHTS = {
    "5205": 0.30, "5206": 0.06, "5207": 0.02,
    "5402": 0.22, "5401": 0.03, "5403": 0.04, "5406": 0.02,
    "5509": 0.20, "5510": 0.05, "5511": 0.04, "5508": 0.02,
}


def _series(base: float, drift: float, vol: float, n: int) -> np.ndarray:
    vals, v = [], base
    for i in range(n):
        shock = rng.normal(0, vol)
        covid = -0.22 if FY[i] == "2020-21" else 0.0
        v = max(0.2, v * (1 + drift + shock + covid))
        vals.append(round(v, 2))
    return np.array(vals)


def annual_commodity_x_country() -> pd.DataFrame:
    """EIDB 'Commodity x Country-wise' layout: HS + country down, FY across."""
    rows = []
    for country, (base, drift, vol) in MARKETS.items():
        country_total = _series(base, drift, vol, len(FY))
        for hs, w in HEADING_WEIGHTS.items():
            jitter = rng.uniform(0.75, 1.25)
            vals = country_total * w * jitter
            row = {"HSCode": hs, "Commodity": YARN_HEADINGS[hs],
                   "Country": country}
            for fy, v in zip(FY, vals):
                row[fy] = round(float(v), 2)
            rows.append(row)
    return pd.DataFrame(rows)


def monthly_commodity_wise() -> pd.DataFrame:
    """MEIDB monthly layout: country down, Mon-YYYY across."""
    months, seasonal = [], []
    # Indian yarn shipping peaks Sep-Nov, troughs Feb-Apr
    idx = {1: 0.94, 2: 0.88, 3: 0.92, 4: 0.90, 5: 0.97, 6: 1.00,
           7: 1.04, 8: 1.08, 9: 1.14, 10: 1.15, 11: 1.09, 12: 0.99}
    for year in range(2021, 2025):
        for m in range(1, 13):
            months.append(f"{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]}-{year}")
            seasonal.append(idx[m])
    seasonal = np.array(seasonal)

    rows = []
    for country, (base, drift, vol) in MARKETS.items():
        monthly_base = base / 12
        trend = np.array([(1 + drift) ** (i / 12) for i in range(len(months))])
        noise = rng.normal(1, vol * 0.5, len(months)).clip(0.5, 1.6)
        vals = monthly_base * trend * seasonal * noise
        row = {"Country": country}
        for mth, v in zip(months, vals):
            row[mth] = round(float(v), 2)
        rows.append(row)
    return pd.DataFrame(rows)



def single_year_all_countries(fy: str = "2024-25") -> pd.DataFrame:
    """EIDB 'Commodity wise all Countries' layout: one HS code, one year.

    Neither the HS code nor the year appears as a column -- they exist only
    in the filename. This is why downloads must be named '<hs>_<fy>.csv'.
    """
    i = FY.index("2024-25") if "2024-25" in FY else len(FY) - 1
    rows = []
    for country, (base, drift, vol) in MARKETS.items():
        v = _series(base, drift, vol, len(FY))[i] * 0.30
        rows.append({"S.No.": len(rows) + 1, "Country": country,
                     "US $ Million": round(float(v), 2)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    a = annual_commodity_x_country()
    a.to_csv(RAW / "SYNTHETIC_eidb_annual_commodity_x_country.csv", index=False)
    print(f"wrote annual sample: {a.shape[0]} rows x {a.shape[1]} cols")

    m = monthly_commodity_wise()
    m.to_csv(RAW / "SYNTHETIC_meidb_monthly.csv", index=False)
    print(f"wrote monthly sample: {m.shape[0]} rows x {m.shape[1]} cols")
    sy = single_year_all_countries()
    sy.to_csv(RAW / "SYNTHETIC_5205_2024-25.csv", index=False)
    print(f"wrote single-year sample: {sy.shape[0]} rows (HS + year from filename)")

    print("\nNOTE: these numbers are invented. Replace with real downloads.")

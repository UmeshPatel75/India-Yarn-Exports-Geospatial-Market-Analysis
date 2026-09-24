"""Turn Tradestat downloads into one tidy long-format table.

Tradestat gives you wide tables -- one column per financial year (EIDB) or
per month (MEIDB). Every downstream step in this project expects long
format instead:

    period | hs_code | hs_desc | country | value_usd_mn

Run this once after dropping your downloads into data/raw/.
"""
from __future__ import annotations

import re
import pandas as pd

from config import RAW, PROCESSED, CANON_COLS, YARN_HEADINGS

# Tradestat year headers look like "2023-2024", "2023-24" or plain "2024".
YEAR_RE = re.compile(r"^\s*(\d{4})\s*[-–]?\s*(\d{2,4})?\s*$")
# MEIDB month headers look like "Apr-2024", "APRIL 2024", "2024-04".
# Matches "Apr-2024", "APRIL 2024", "2024-04" and MEIDB's revision-tagged
# "Mar-2025 (R)". Deliberately does NOT match cumulative columns such as
# "Jan-Mar 2025 (R)" -- those would double-count against the monthly figures.
MONTH_RE = re.compile(
    r"^\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
    r"[\s\-/]*(\d{4})\s*(?:\((?:R|F|P)\))?\s*$",
    re.I,
)
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def _classify_column(name: str) -> tuple[str, str] | None:
    """Return ('period', normalised_label) if this column holds a value."""
    s = str(name).strip()
    m = MONTH_RE.match(s)
    if m:
        return "month", f"{m.group(2)}-{MONTHS[m.group(1)[:3].lower()]:02d}"
    m = YEAR_RE.match(s)
    if m:
        start = m.group(1)
        end = m.group(2)
        if end and len(end) == 2:
            return "year", f"{start}-{end}"
        if end and len(end) == 4:
            return "year", f"{start}-{end[2:]}"
        return "year", start
    return None


def infer_from_filename(path) -> tuple[str | None, str | None]:
    """Pull HS code and period out of a filename.

    The 'Commodity wise all Countries' report returns one HS code for one
    year, so neither appears as a column -- they are only in whatever you
    named the file. Name downloads like '5205_2023-24.csv' and this
    recovers both.
    """
    stem = str(path).replace("\\", "/").split("/")[-1]
    stem = stem.rsplit(".", 1)[0]

    hs = None
    m = re.search(r"(?<!\d)(\d{4})(?!\d)", stem)
    if m and m.group(1)[:2] in {"52", "54", "55"}:
        hs = m.group(1)

    period = None
    m = re.search(r"(20\d{2})\s*[-_]\s*(\d{2,4})", stem)
    if m:
        end = m.group(2)
        period = f"{m.group(1)}-{end[-2:]}"
    return hs, period


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lowered = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        for key, original in lowered.items():
            if cand in key:
                return original
    return None


def _locate_header(path) -> tuple[int, str | None]:
    """Find the real header row and the stated value unit.

    Tradestat exports carry two title rows above the table:
        row 0: TradeStat->Eidb->Export->Commodity-wise-all-countries
        row 1: Report Generated on: ... Values in US $ Million|| Values in Quantity
        row 2: S.No. | Country / Region | 2017-2018 | 2018-2019 | %Growth | ...
    """
    if str(path).lower().endswith((".xlsx", ".xls")):
        probe = pd.read_excel(path, header=None, nrows=12)
    else:
        probe = pd.read_csv(path, header=None, nrows=12,
                            on_bad_lines="skip")

    unit = None
    header_row = 0
    for i, row in probe.iterrows():
        joined = " ".join(str(v) for v in row.tolist() if pd.notna(v))
        low = joined.lower()
        if unit is None:
            if "crore" in low and "us $" not in low:
                unit = "INR Crore"
            elif "us $" in low or "us$" in low:
                unit = "US $ Million"
        # EIDB uses "S.No." and "Country / Region"; MEIDB uses "S." and
        # "HS Code" / "Commodity" with no country column at all.
        # Require several populated cells so the one-cell title rows
        # (which contain the word "Commoditywise") are not mistaken
        # for the header.
        populated = int(row.notna().sum())
        if populated >= 3 and (
            "country" in low or "s.no" in low
            or "hs code" in low or "hscode" in low
            or "commodity" in low
        ):
            header_row = i
            break
    return header_row, unit


def tidy_tradestat(path, default_hs: str | None = None) -> pd.DataFrame:
    """Read one Tradestat CSV/XLSX and return it in canonical long format.

    Copes with the real export layout: two title rows, a 'Country / Region'
    column, and value columns duplicated because the report emits a Value
    block followed by a Quantity block. Only the first (Value) block is
    kept -- pandas suffixes the repeats with '.1', which we skip.
    """
    path_s = str(path)
    header_row, unit = _locate_header(path_s)

    if path_s.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path_s, header=header_row)
    else:
        df = pd.read_csv(path_s, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]

    if unit == "INR Crore":
        print(f"    ! {path.name if hasattr(path,'name') else path_s}: "
              f"values are in Rs Crore, not US $ Million. Re-download.")

    country_col = _find_column(df, ["country", "partner", "destination"])
    hs_col = _find_column(df, ["hscode", "hs code", "hs_code", "itc"])
    desc_col = _find_column(df, ["commodity", "description", "product"])

    file_hs, file_period = infer_from_filename(path_s)

    # Collect period columns, stopping at the Quantity block. Pandas renames
    # duplicated headers with a '.1' suffix, so those are skipped naturally;
    # we also stop if a period label repeats.
    value_cols, labels, seen = [], {}, set()
    for col in df.columns:
        if col.endswith(".1") or "%" in col:
            continue
        hit = _classify_column(col)
        if not hit:
            continue
        if hit[1] in seen:
            break
        seen.add(hit[1])
        value_cols.append(col)
        labels[col] = hit[1]

    if not value_cols:
        val_col = _find_column(
            df, ["us $", "us$", "value", "million", "crore", "amount"])
        if val_col is None or not file_period:
            raise ValueError(
                f"Cannot determine period for {path_s}. Columns found: "
                f"{list(df.columns)}")
        value_cols = [val_col]
        labels[val_col] = file_period

    long = df.melt(
        id_vars=[c for c in (country_col, hs_col, desc_col) if c],
        value_vars=value_cols,
        var_name="_col",
        value_name="value_usd_mn",
    )
    long["period"] = long["_col"].map(labels)
    long = long.drop(columns="_col")

    # MEIDB commodity-wise has no country column: it reports India totals.
    # Use a label the total-row filter below will not strip out.
    long["country"] = (long[country_col].astype(str).str.strip()
                       if country_col else "ALL DESTINATIONS")
    long["hs_code"] = (long[hs_col].astype(str).str.strip()
                       .str.replace(r"\.0$", "", regex=True)
                       if hs_col else (default_hs or file_hs or "ALL"))
    long["hs_desc"] = long[desc_col].astype(str).str.strip() if desc_col else ""

    # Nil is a bare '-'. Do NOT strip '-' generally: it would flip signs.
    vals = (long["value_usd_mn"].astype(str)
            .str.replace(",", "", regex=False).str.strip())
    vals = vals.replace({"-": None, "": None, "nan": None,
                         "NA": None, "N.A.": None})
    long["value_usd_mn"] = pd.to_numeric(vals, errors="coerce")

    long = long[CANON_COLS]
    mask = ~long["country"].str.contains(
        r"total|^all$|^nan$|unspecified", case=False, regex=True, na=True)
    # MEIDB appends an "India's Total Export" row carrying no HS code.
    if hs_col:
        codes = long["hs_code"].astype(str).str.strip().str.lower()
        mask &= ~codes.isin(["nan", "none", ""])
    mask &= ~long["hs_desc"].astype(str).str.contains(
        r"total export", case=False, regex=True, na=False)
    long = long[mask & long["value_usd_mn"].notna()]
    return long.reset_index(drop=True)


def filter_yarn(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the 4-digit headings that are genuinely yarn."""
    heading = df["hs_code"].astype(str).str[:4]
    out = df[heading.isin(YARN_HEADINGS)].copy()
    out["heading"] = heading[heading.isin(YARN_HEADINGS)]
    out["heading_desc"] = out["heading"].map(YARN_HEADINGS)
    out["chapter"] = out["heading"].str[:2]
    return out


def build(pattern: str = "*") -> pd.DataFrame:
    """Tidy every file in data/raw/, concatenate, and save."""
    files = [p for p in RAW.glob(pattern)
             if p.suffix.lower() in {".csv", ".xlsx", ".xls"}]
    if not files:
        raise FileNotFoundError(
            f"No data files in {RAW}. See docs/DATA_COLLECTION.md.")

    frames = []
    for f in files:
        try:
            frames.append(tidy_tradestat(f))
            print(f"  parsed {f.name}")
        except Exception as exc:  # keep going; report at the end
            print(f"  SKIPPED {f.name}: {exc}")

    if not frames:
        raise ValueError("Nothing could be parsed.")

    combined = pd.concat(frames, ignore_index=True)

    # Each Tradestat download reports the selected year AND the prior year,
    # so consecutive files overlap. Deduplicate on the natural key, keeping
    # the last occurrence -- the more recently downloaded file carries the
    # more recent revision.
    before = len(combined)
    combined = combined.drop_duplicates(
        subset=["period", "hs_code", "country"], keep="last")
    dropped = before - len(combined)

    combined = combined.sort_values(["hs_code", "period", "country"])
    out = PROCESSED / "exports_long.csv"
    combined.to_csv(out, index=False)

    print(f"\n{len(combined):,} rows -> {out}")
    if dropped:
        print(f"  ({dropped:,} overlapping rows removed -- each download "
              f"covers two years)")
    print(f"  HS codes: {sorted(combined['hs_code'].unique())}")
    print(f"  Periods:  {sorted(combined['period'].unique())}")
    print(f"  Countries: {combined['country'].nunique()}")
    return combined


if __name__ == "__main__":
    build()

"""Diagnostic: dump the raw structure of files in data/raw/.

Run this when ingest reports 'parsed' but produces 0 rows. It shows what
the file actually contains before any parsing logic touches it.

    py src\\inspect_raw.py
"""
from __future__ import annotations

import sys

import pandas as pd

from config import RAW


def inspect(path, n_rows: int = 8) -> None:
    print("=" * 70)
    print(f"FILE: {path.name}")
    print("=" * 70)

    try:
        if path.suffix.lower() in (".xlsx", ".xls"):
            xl = pd.ExcelFile(path)
            print(f"Sheets: {xl.sheet_names}")
            raw = pd.read_excel(path, header=None, nrows=n_rows + 6)
        else:
            raw = pd.read_csv(path, header=None, nrows=n_rows + 6,
                              on_bad_lines="skip")
    except Exception as exc:
        print(f"  COULD NOT READ: {exc}")
        return

    print(f"\nShape of first rows read: {raw.shape}")
    print("\n--- RAW CELLS, no header assumed (row index on left) ---")
    with pd.option_context("display.max_columns", 30,
                           "display.width", 200,
                           "display.max_colwidth", 28):
        print(raw.head(n_rows + 6).to_string())

    print("\n--- WHAT PANDAS PICKS AS HEADERS (header=0) ---")
    try:
        df = pd.read_excel(path) if path.suffix.lower() in (".xlsx", ".xls") \
            else pd.read_csv(path)
        print(f"Columns: {list(df.columns)}")
        print(f"Dtypes:\n{df.dtypes.to_string()}")
        print(f"\nFirst 5 rows:")
        with pd.option_context("display.max_columns", 30, "display.width", 200):
            print(df.head(5).to_string())
    except Exception as exc:
        print(f"  {exc}")
    print()


def main() -> None:
    files = sorted(p for p in RAW.glob("*")
                   if p.suffix.lower() in {".csv", ".xlsx", ".xls"})
    if not files:
        print(f"No files in {RAW}")
        return
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"Found {len(files)} files. Inspecting first {limit}.\n")
    for p in files[:limit]:
        inspect(p)


if __name__ == "__main__":
    main()

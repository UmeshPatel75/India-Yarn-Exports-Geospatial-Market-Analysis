import sys, pandas as pd
sys.path.insert(0, 'src')
from pathlib import Path
import ingest

f = sorted(Path('data/raw').glob('5509*'))[0]
print("FILE:", f.name)

raw = pd.read_excel(f, header=None, nrows=6)
with pd.option_context('display.max_columns', 20, 'display.width', 250,
                       'display.max_colwidth', 30):
    print(raw.to_string())

print("\n--- after parsing ---")
d = ingest.tidy_tradestat(f)
print("rows returned:", len(d))
if len(d):
    print(d.head().to_string())
    print("hs codes:", d.hs_code.unique())
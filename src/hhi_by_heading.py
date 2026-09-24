import sys
sys.path.insert(0, 'src')
import pandas as pd
import analysis as an

d = pd.read_csv('data/processed/exports_long.csv')
d['hs_code'] = d['hs_code'].astype(str).str.strip()

for code in ['5205', '5402', '5509']:
    sub = d[d['hs_code'] == code]
    h = an.hhi(sub)
    first, last = h.iloc[0], h.iloc[-1]
    print(f"HS {code}:  {first['period']} HHI {first['hhi']:>6,.0f}"
          f"   ->  {last['period']} HHI {last['hhi']:>6,.0f}"
          f"   ({last['concentration']})")
    print(f"          top market {last['top1_market']} at {last['top1_share_pct']:.1f}%")

h = an.hhi(d)
print(f"\nCombined: {h.iloc[0]['period']} HHI {h.iloc[0]['hhi']:,.0f}"
      f"  ->  {h.iloc[-1]['period']} HHI {h.iloc[-1]['hhi']:,.0f}")
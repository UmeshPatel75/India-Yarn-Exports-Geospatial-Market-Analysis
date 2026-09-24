import pandas as pd
d = pd.read_csv('data/processed/exports_long.csv')
d['hs_code'] = d['hs_code'].astype(str).str.strip()

sub = d[(d['hs_code'] == '5402') & (d['period'] == '2025-26')]
print(f"HS 5402, FY 2025-26 (EIDB): {sub['value_usd_mn'].sum():,.2f} US$ mn")
print(f"MEIDB Apr-Mar 2026 showed:   634.37 US$ mn")
print(f"Destinations: {sub['country'].nunique()}")
print()
print("Headings present:", sorted(d['hs_code'].unique()))
print("Periods present:", sorted(d['period'].unique()))
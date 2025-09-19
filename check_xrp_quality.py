import pandas as pd

# Load the new XRPUSD data
df = pd.read_csv('CSVdata/raw/GEN_XRPUSD_M1_1month.csv')
df['datetime'] = pd.to_datetime(df['time'])

print(f'XRPUSD New Download: {len(df)} records')
print(f'Date range: {df["datetime"].min()} to {df["datetime"].max()}')

# Check for time gaps > 5 minutes
gaps = df['datetime'].diff() > pd.Timedelta(minutes=5)
print(f'Time gaps > 5min: {gaps.sum()}')

if gaps.sum() > 0:
    print('Gap details:')
    for i, idx in enumerate(df[gaps].index):
        gap_start = df.iloc[idx]['datetime']
        gap_prev = df.iloc[idx-1]['datetime']
        gap_duration = (gap_start - gap_prev).total_seconds() / 60
        print(f'  Gap {i+1}: {gap_duration:.1f} minutes from {gap_prev} to {gap_start}')
else:
    print('✅ No significant time gaps found!')

# Check for spread issues (old XRPUSD had 27-28% spreads)
print(f'\nSpread analysis:')
print(f'Spread values: {df["spread"].unique()}')
spreads_as_percent = (df['spread'] / df['close'] * 100)
print(f'Spread as % of price: min={spreads_as_percent.min():.4f}%, max={spreads_as_percent.max():.4f}%, avg={spreads_as_percent.mean():.4f}%')

excessive_spreads = spreads_as_percent > 10  # Much lower threshold than old 27%
print(f'Excessive spreads (>10%): {excessive_spreads.sum()}')

print(f'\nComparison with old XRPUSD:')
print(f'New: 43,192 bars vs Old: 35,755 bars')
print(f'Improvement: +{43192 - 35755} bars ({((43192 - 35755) / 35755 * 100):.1f}%)')
print(f'Old had: 1 critical gap (7438 min = 5+ days) + 35,755 spread issues')
print(f'New has: {gaps.sum()} time gaps, {excessive_spreads.sum()} spread issues')
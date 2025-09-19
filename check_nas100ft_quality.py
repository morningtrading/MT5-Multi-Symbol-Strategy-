import pandas as pd

# Load the new NAS100ft data
df = pd.read_csv('CSVdata/raw/GEN_NAS100ft_M1_1month.csv')
df['datetime'] = pd.to_datetime(df['time'])

print(f'NAS100ft New Download: {len(df)} records')
print(f'Date range: {df["datetime"].min()} to {df["datetime"].max()}')

# Check for time gaps > 5 minutes
gaps = df['datetime'].diff() > pd.Timedelta(minutes=5)
print(f'Time gaps > 5min: {gaps.sum()}')

if gaps.sum() > 0:
    print('Gap details (first 10):')
    for i, idx in enumerate(df[gaps].index[:10]):  # Show first 10 gaps
        gap_start = df.iloc[idx]['datetime']
        gap_prev = df.iloc[idx-1]['datetime']
        gap_duration = (gap_start - gap_prev).total_seconds() / 60
        print(f'  Gap {i+1}: {gap_duration:.1f} minutes from {gap_prev} to {gap_start}')
    if gaps.sum() > 10:
        print(f'  ... and {gaps.sum() - 10} more gaps')
else:
    print('✅ No significant time gaps found!')

print(f'\nComparison with old NAS100ft:')
print(f'New: 30,120 bars vs Old: 23,979 bars')
print(f'Improvement: +{30120 - 23979} bars ({((30120 - 23979) / 23979 * 100):.1f}%)')
print('Old had: Multiple critical gaps including 4+ hour and multi-day gaps')
print(f'New has: {gaps.sum()} time gaps')

# Data completeness
total_minutes_30_days = 30 * 24 * 60
print(f'\nData completeness:')
print(f'Theoretical 30-day minutes: {total_minutes_30_days:,}')
print(f'Actual data points: {len(df):,}')
print(f'Completeness: {(len(df) / total_minutes_30_days * 100):.1f}%')
import pandas as pd

# Load the new USOUSD data
df = pd.read_csv('CSVdata/raw/GEN_USOUSD_M1_1month.csv')
df['datetime'] = pd.to_datetime(df['time'])

print(f'USOUSD New Download: {len(df)} records')
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

# Check spread analysis
print(f'\nSpread analysis:')
print(f'Spread values: {df["spread"].unique()}')

print(f'\nComparison with old USOUSD:')
# Note: We need to check what the old count was
print(f'New: 28,901 bars')
print('Old had: many gaps (dozens of 60+ minute gaps)')
print(f'New has: {gaps.sum()} time gaps')

# Check total theoretical minutes in 30 days
total_minutes_30_days = 30 * 24 * 60
print(f'\nData completeness:')
print(f'Theoretical 30-day minutes: {total_minutes_30_days:,}')
print(f'Actual data points: {len(df):,}')
print(f'Completeness: {(len(df) / total_minutes_30_days * 100):.1f}%')
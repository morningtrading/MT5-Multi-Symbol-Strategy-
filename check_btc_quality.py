import pandas as pd

# Load the new BTCUSD data
df = pd.read_csv('CSVdata/raw/GEN_BTCUSD_M1_1month.csv')
df['datetime'] = pd.to_datetime(df['time'])

print(f'BTCUSD New Download: {len(df)} records')
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
    
print(f'\nComparison with old BTCUSD:')
print(f'New: 43,191 bars vs Old: 41,752 bars')
print(f'Improvement: +{43191 - 41752} bars ({((43191 - 41752) / 41752 * 100):.1f}%)')
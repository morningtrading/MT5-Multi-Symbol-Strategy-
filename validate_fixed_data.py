#!/usr/bin/env python3
"""
Validation script for gap-filled data
"""
import pandas as pd
import os
from datetime import timedelta

def validate_fixed_data():
    print('✅ VALIDATING FIXED DATA QUALITY')
    print('=' * 50)
    
    fixed_dir = "CSVdata/fixed"
    
    if not os.path.exists(fixed_dir):
        print('❌ Fixed directory not found!')
        return
    
    fixed_files = [f for f in os.listdir(fixed_dir) if f.endswith('_fixed.csv')]
    
    if not fixed_files:
        print('❌ No fixed files found!')
        return
    
    print(f'📁 Found {len(fixed_files)} fixed files')
    
    for filename in fixed_files:
        symbol = filename.replace('GEN_', '').replace('_M1_1month_fixed.csv', '')
        
        print(f'\n📊 Validating {symbol}...')
        
        # Load fixed data
        fixed_path = os.path.join(fixed_dir, filename)
        df = pd.read_csv(fixed_path)
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Check for gaps
        df['time_diff'] = df['time'].diff()
        expected_interval = timedelta(minutes=1)
        tolerance = timedelta(seconds=30)
        
        remaining_gaps = df[df['time_diff'] > expected_interval + tolerance]
        
        # Validation checks
        total_bars = len(df)
        gaps_remaining = len(remaining_gaps)
        date_range = (df['time'].min(), df['time'].max())
        
        # Check for invalid data
        invalid_prices = df[(df['open'] <= 0) | (df['high'] <= 0) | (df['low'] <= 0) | (df['close'] <= 0)]
        ohlc_violations = df[(df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | (df['low'] > df['open']) | (df['low'] > df['close'])]
        
        print(f'   📈 Total bars: {total_bars:,}')
        print(f'   📅 Date range: {date_range[0].strftime("%Y-%m-%d")} to {date_range[1].strftime("%Y-%m-%d")}')
        print(f'   🕳️ Remaining gaps: {gaps_remaining}')
        print(f'   ❌ Invalid prices: {len(invalid_prices)}')
        print(f'   ⚠️  OHLC violations: {len(ohlc_violations)}')
        
        # Calculate data quality score
        if gaps_remaining == 0 and len(invalid_prices) == 0 and len(ohlc_violations) == 0:
            print(f'   ✅ Status: PERFECT - No issues found')
        elif gaps_remaining == 0:
            print(f'   🟡 Status: GOOD - No gaps, minor data issues')
        else:
            print(f'   🔴 Status: ISSUES - {gaps_remaining} gaps still remain')

if __name__ == "__main__":
    validate_fixed_data()
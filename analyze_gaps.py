#!/usr/bin/env python3
"""
Gap Analysis Script - Determine if gaps are from market closures or missing data
"""
import pandas as pd
from datetime import datetime, timedelta
import os

def analyze_gaps():
    print('🔍 ANALYZING GAP PATTERNS IN CSV DATA')
    print('=' * 60)
    
    # Analyze USOUSD file (worst case with 1,212 issues)
    csv_path = 'CSVdata/raw/GEN_USOUSD_M1_1month.csv'
    
    if not os.path.exists(csv_path):
        print('❌ USOUSD CSV file not found!')
        return
    
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    print(f'📊 ANALYZING: {csv_path}')
    print(f'Total records: {len(df):,}')
    print(f'Date range: {df["time"].min()} to {df["time"].max()}')
    
    # Calculate time differences
    df['time_diff'] = df['time'].diff()
    
    # Find gaps (more than 1 minute + 30 seconds tolerance)
    expected_interval = timedelta(minutes=1)
    tolerance = timedelta(seconds=30)
    gaps = df[df['time_diff'] > expected_interval + tolerance].copy()
    
    print(f'\nGaps found: {len(gaps)}')
    
    if len(gaps) == 0:
        print('✅ No gaps found!')
        return
    
    print('\n🕐 FIRST 15 GAPS ANALYSIS:')
    print('Time Before Gap        -> Gap Size -> Day of Week -> Hour')
    print('-' * 70)
    
    for i, (idx, row) in enumerate(gaps.head(15).iterrows()):
        if idx > 0:  # Make sure we have a previous row
            prev_time = df.loc[idx-1, 'time']
            gap_minutes = row['time_diff'].total_seconds() / 60
            
            # Get day of week and hour info
            day_of_week = prev_time.strftime('%A')
            hour = prev_time.hour
            
            print(f'{prev_time.strftime("%Y-%m-%d %H:%M")} -> {gap_minutes:4.0f}min -> {day_of_week:9} -> {hour:02d}h')
    
    # Analyze gaps by day of week
    print('\n🗓️ GAP ANALYSIS BY DAY OF WEEK:')
    gap_days = {}
    weekend_gaps = 0
    weekday_gaps = 0
    
    for idx, row in gaps.iterrows():
        if idx > 0:
            prev_time = df.loc[idx-1, 'time']
            day_name = prev_time.strftime('%A')
            hour = prev_time.hour
            
            if day_name not in gap_days:
                gap_days[day_name] = []
            gap_days[day_name].append(hour)
            
            # Count weekend vs weekday gaps
            if day_name in ['Saturday', 'Sunday']:
                weekend_gaps += 1
            else:
                weekday_gaps += 1
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        if day in gap_days:
            hours = gap_days[day]
            avg_hour = sum(hours) / len(hours) if hours else 0
            print(f'{day:9}: {len(hours):3} gaps (avg hour: {avg_hour:4.1f})')
        else:
            print(f'{day:9}: {0:3} gaps')
    
    print(f'\n📊 GAP TYPE DISTRIBUTION:')
    total_gaps = weekend_gaps + weekday_gaps
    if total_gaps > 0:
        print(f'Weekend gaps: {weekend_gaps:3} ({weekend_gaps/total_gaps*100:4.1f}%)')
        print(f'Weekday gaps: {weekday_gaps:3} ({weekday_gaps/total_gaps*100:4.1f}%)')
    
    # Analyze gap sizes
    gap_sizes = []
    for idx, row in gaps.iterrows():
        if idx > 0:
            gap_minutes = row['time_diff'].total_seconds() / 60
            gap_sizes.append(gap_minutes)
    
    if gap_sizes:
        gap_sizes = pd.Series(gap_sizes)
        print(f'\n⏱️ GAP SIZE ANALYSIS:')
        print(f'Min gap:     {gap_sizes.min():6.1f} minutes')
        print(f'Max gap:     {gap_sizes.max():6.1f} minutes') 
        print(f'Avg gap:     {gap_sizes.mean():6.1f} minutes')
        print(f'Median gap:  {gap_sizes.median():6.1f} minutes')
        
        # Common gap sizes
        print(f'\n📏 MOST COMMON GAP SIZES:')
        gap_size_counts = gap_sizes.value_counts().head(8)
        for size, count in gap_size_counts.items():
            print(f'{size:6.0f} min gaps: {count:3} times')
        
        # Analyze by hour patterns
        print(f'\n🕐 GAP PATTERNS BY HOUR:')
        hour_gaps = {}
        for idx, row in gaps.iterrows():
            if idx > 0:
                prev_time = df.loc[idx-1, 'time']
                hour = prev_time.hour
                gap_minutes = row['time_diff'].total_seconds() / 60
                
                if hour not in hour_gaps:
                    hour_gaps[hour] = []
                hour_gaps[hour].append(gap_minutes)
        
        # Show hours with most gaps
        hour_gap_counts = {hour: len(gaps_list) for hour, gaps_list in hour_gaps.items()}
        sorted_hours = sorted(hour_gap_counts.items(), key=lambda x: x[1], reverse=True)
        
        for hour, count in sorted_hours[:10]:
            avg_gap = sum(hour_gaps[hour]) / len(hour_gaps[hour])
            print(f'Hour {hour:02d}: {count:3} gaps (avg: {avg_gap:5.1f} min)')

    # Determine gap type
    print(f'\n🧐 GAP ANALYSIS CONCLUSION:')
    
    # Weekend gap percentage
    weekend_pct = weekend_gaps / total_gaps * 100 if total_gaps > 0 else 0
    
    # Check for market closure patterns (Friday evening to Sunday evening)
    friday_evening_gaps = 0
    sunday_evening_gaps = 0
    random_gaps = 0
    
    for idx, row in gaps.iterrows():
        if idx > 0:
            prev_time = df.loc[idx-1, 'time']
            day_name = prev_time.strftime('%A')
            hour = prev_time.hour
            gap_minutes = row['time_diff'].total_seconds() / 60
            
            # Friday evening (after 17:00) with large gaps = market closure
            if day_name == 'Friday' and hour >= 17 and gap_minutes > 120:
                friday_evening_gaps += 1
            # Sunday evening gaps = market opening
            elif day_name == 'Sunday' and hour >= 17:
                sunday_evening_gaps += 1
            # Small gaps during trading hours = likely missing data
            elif day_name not in ['Saturday', 'Sunday'] and gap_minutes < 60:
                random_gaps += 1
    
    print(f'🔸 Weekend/closure-related gaps: ~{weekend_pct:.0f}%')
    print(f'🔸 Friday evening market close gaps: {friday_evening_gaps}')
    print(f'🔸 Sunday evening market open gaps: {sunday_evening_gaps}')
    print(f'🔸 Likely random missing data: {random_gaps}')
    
    # Final verdict
    if weekend_pct > 70:
        print(f'\n✅ VERDICT: Mostly legitimate market closures')
        print(f'   The gaps appear to be from weekend market closures, which is normal.')
    elif random_gaps > total_gaps * 0.3:
        print(f'\n⚠️  VERDICT: Significant missing data issues')
        print(f'   Many gaps during trading hours suggest data collection problems.')
    else:
        print(f'\n🤔 VERDICT: Mixed - both market closures and missing data')
        print(f'   Some legitimate closures, but also apparent data collection gaps.')

if __name__ == "__main__":
    analyze_gaps()
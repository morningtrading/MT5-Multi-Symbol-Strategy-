#!/usr/bin/env python3
"""
Data Gap Filler - Multiple Strategies for Missing Minute Bars
===========================================================

Provides various methods to fill missing minute bars in MT5 CSV data:
1. Forward Fill (carry previous values)
2. Linear Interpolation (smooth transitions)
3. Flat Interpolation (constant OHLC)
4. Zero Volume Fill (mark as inactive periods)

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from typing import Literal, Optional
import warnings
warnings.filterwarnings('ignore')

class DataGapFiller:
    """Comprehensive data gap filling for MT5 minute bar data"""
    
    def __init__(self, data_dir: str = "CSVdata"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.fixed_dir = os.path.join(data_dir, "fixed")
        
        # Create fixed directory if it doesn't exist
        os.makedirs(self.fixed_dir, exist_ok=True)
        
        self.fill_stats = {
            "files_processed": 0,
            "total_gaps_filled": 0,
            "processing_time": 0.0
        }
    
    def detect_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect gaps in minute bar data"""
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Calculate time differences
        df['time_diff'] = df['time'].diff()
        expected_interval = timedelta(minutes=1)
        tolerance = timedelta(seconds=30)
        
        # Find gaps
        gaps = df[df['time_diff'] > expected_interval + tolerance].copy()
        
        return gaps
    
    def fill_gaps_forward_fill(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strategy 1: Forward Fill (Carry Previous Values)
        
        Best for: Conservative backtesting, avoiding artificial movements
        - OHLC = previous bar's close price
        - Volume = 0 (no activity)
        - Spread = previous bar's spread
        """
        print("   Using Forward Fill strategy...")
        
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Create complete minute range
        start_time = df['time'].min()
        end_time = df['time'].max()
        complete_range = pd.date_range(start=start_time, end=end_time, freq='1min')
        
        # Reindex with complete range
        df.set_index('time', inplace=True)
        df = df.reindex(complete_range)
        
        # Forward fill most values
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].fillna(method='ffill')
        df['spread'] = df['spread'].fillna(method='ffill')
        
        # Set volume to 0 for filled bars (indicates no trading activity)
        df['tick_volume'] = df['tick_volume'].fillna(0)
        df['real_volume'] = df['real_volume'].fillna(0)
        
        # Reset index
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'time'}, inplace=True)
        
        return df
    
    def fill_gaps_linear_interpolation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strategy 2: Linear Interpolation
        
        Best for: Trend analysis, smooth price transitions
        - OHLC values interpolated linearly between known points
        - Volume distributed proportionally
        - Creates artificial but smooth movements
        """
        print("   Using Linear Interpolation strategy...")
        
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Create complete minute range
        start_time = df['time'].min()
        end_time = df['time'].max()
        complete_range = pd.date_range(start=start_time, end=end_time, freq='1min')
        
        # Reindex with complete range
        df.set_index('time', inplace=True)
        df = df.reindex(complete_range)
        
        # Linear interpolation for price data
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].interpolate(method='linear')
        df['spread'] = df['spread'].interpolate(method='linear')
        
        # Distribute volume proportionally (or set to average)
        avg_volume = df['tick_volume'].mean()
        df['tick_volume'] = df['tick_volume'].fillna(avg_volume / 10)  # Reduced volume for filled bars
        df['real_volume'] = df['real_volume'].fillna(0)
        
        # Reset index
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'time'}, inplace=True)
        
        return df
    
    def fill_gaps_flat_interpolation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strategy 3: Flat Interpolation (Constant OHLC)
        
        Best for: Range-bound markets, avoiding false breakouts
        - OHLC = previous close (flat price action)
        - Volume = 0 (no activity)
        - Maintains price level without movement
        """
        print("   Using Flat Interpolation strategy...")
        
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Create complete minute range
        start_time = df['time'].min()
        end_time = df['time'].max()
        complete_range = pd.date_range(start=start_time, end=end_time, freq='1min')
        
        # Reindex with complete range
        df.set_index('time', inplace=True)
        df = df.reindex(complete_range)
        
        # Forward fill to get the last known close
        df['close'] = df['close'].fillna(method='ffill')
        
        # For filled bars, set OHLC all equal to close (flat bars)
        filled_mask = df['open'].isna()
        df.loc[filled_mask, 'open'] = df.loc[filled_mask, 'close']
        df.loc[filled_mask, 'high'] = df.loc[filled_mask, 'close']
        df.loc[filled_mask, 'low'] = df.loc[filled_mask, 'close']
        
        # Fill remaining values
        df['spread'] = df['spread'].fillna(method='ffill')
        df['tick_volume'] = df['tick_volume'].fillna(0)
        df['real_volume'] = df['real_volume'].fillna(0)
        
        # Reset index
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'time'}, inplace=True)
        
        return df
    
    def fill_gaps_smart_interpolation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Strategy 4: Smart Interpolation (Hybrid Approach)
        
        Best for: Most realistic backtesting
        - Small gaps (≤5 min): Linear interpolation
        - Large gaps (>5 min): Forward fill (market likely inactive)
        - Volume handling based on gap size
        """
        print("   Using Smart Interpolation strategy...")
        
        df = df.copy()
        df['time'] = pd.to_datetime(df['time'])
        df = df.sort_values('time')
        
        # Detect gaps first
        gaps = self.detect_gaps(df)
        
        # Create complete minute range
        start_time = df['time'].min()
        end_time = df['time'].max()
        complete_range = pd.date_range(start=start_time, end=end_time, freq='1min')
        
        # Reindex with complete range
        df.set_index('time', inplace=True)
        original_data_mask = ~df['open'].isna()  # Mark original data points
        df = df.reindex(complete_range)
        
        # Identify gap sizes
        df['gap_size'] = 0
        for _, gap_row in gaps.iterrows():
            gap_start_idx = df.index.get_loc(gap_row['time'])
            prev_time = df.index[gap_start_idx - 1] if gap_start_idx > 0 else None
            if prev_time:
                gap_minutes = (gap_row['time'] - prev_time).total_seconds() / 60
                # Mark all minutes in this gap
                gap_range = pd.date_range(start=prev_time + timedelta(minutes=1), 
                                        end=gap_row['time'] - timedelta(minutes=1), freq='1min')
                for gap_time in gap_range:
                    if gap_time in df.index:
                        df.loc[gap_time, 'gap_size'] = gap_minutes
        
        # Apply different strategies based on gap size
        small_gap_mask = (df['gap_size'] > 0) & (df['gap_size'] <= 5)
        large_gap_mask = (df['gap_size'] > 5)
        
        # For small gaps: Linear interpolation
        if small_gap_mask.any():
            df.loc[small_gap_mask, ['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].interpolate(method='linear')
        
        # For large gaps: Forward fill
        df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].fillna(method='ffill')
        
        # Handle spread and volume
        df['spread'] = df['spread'].fillna(method='ffill')
        df.loc[small_gap_mask, 'tick_volume'] = df['tick_volume'].mean() / 5  # Reduced volume
        df.loc[large_gap_mask, 'tick_volume'] = 0  # No volume for large gaps
        df['tick_volume'] = df['tick_volume'].fillna(0)
        df['real_volume'] = df['real_volume'].fillna(0)
        
        # Clean up temporary column
        df.drop('gap_size', axis=1, inplace=True)
        
        # Reset index
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'time'}, inplace=True)
        
        return df
    
    def process_file(self, symbol: str, 
                    strategy: Literal["forward_fill", "linear", "flat", "smart"] = "smart",
                    backup_original: bool = True) -> bool:
        """Process a single CSV file to fill gaps"""
        
        input_file = os.path.join(self.raw_dir, f"GEN_{symbol}_M1_1month.csv")
        output_file = os.path.join(self.fixed_dir, f"GEN_{symbol}_M1_1month_fixed.csv")
        
        if not os.path.exists(input_file):
            print(f"❌ File not found: {input_file}")
            return False
        
        try:
            # Load data
            print(f"📊 Processing {symbol}...")
            df = pd.read_csv(input_file)
            original_count = len(df)
            
            # Detect gaps before filling
            gaps_before = self.detect_gaps(df)
            gap_count = len(gaps_before)
            
            if gap_count == 0:
                print(f"   ✅ No gaps found in {symbol}")
                return True
            
            print(f"   🔍 Found {gap_count} gaps to fill")
            
            # Apply selected strategy
            if strategy == "forward_fill":
                df_fixed = self.fill_gaps_forward_fill(df)
            elif strategy == "linear":
                df_fixed = self.fill_gaps_linear_interpolation(df)
            elif strategy == "flat":
                df_fixed = self.fill_gaps_flat_interpolation(df)
            elif strategy == "smart":
                df_fixed = self.fill_gaps_smart_interpolation(df)
            else:
                raise ValueError(f"Unknown strategy: {strategy}")
            
            # Calculate filled bars
            bars_added = len(df_fixed) - original_count
            
            # Save fixed data
            df_fixed.to_csv(output_file, index=False)
            
            # Update stats
            self.fill_stats["files_processed"] += 1
            self.fill_stats["total_gaps_filled"] += bars_added
            
            print(f"   ✅ Fixed {gap_count} gaps, added {bars_added} bars")
            print(f"   💾 Saved to: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error processing {symbol}: {e}")
            return False
    
    def process_all_files(self, 
                         strategy: Literal["forward_fill", "linear", "flat", "smart"] = "smart",
                         symbols: Optional[list] = None) -> dict:
        """Process all CSV files in the raw directory"""
        
        print(f"🔧 DATA GAP FILLER")
        print(f"=" * 60)
        print(f"Strategy: {strategy.upper()}")
        print(f"Input dir: {self.raw_dir}")
        print(f"Output dir: {self.fixed_dir}")
        print(f"=" * 60)
        
        import time
        start_time = time.time()
        
        # Get list of files to process
        if symbols:
            files = [f"GEN_{symbol}_M1_1month.csv" for symbol in symbols]
        else:
            files = [f for f in os.listdir(self.raw_dir) if f.endswith('.csv') and f.startswith('GEN_')]
        
        if not files:
            print("❌ No CSV files found to process")
            return {}
        
        print(f"📁 Found {len(files)} files to process")
        
        results = {}
        success_count = 0
        
        for filename in files:
            # Extract symbol from filename
            symbol = filename.replace('GEN_', '').replace('_M1_1month.csv', '')
            
            success = self.process_file(symbol, strategy)
            results[symbol] = success
            
            if success:
                success_count += 1
        
        # Final summary
        processing_time = time.time() - start_time
        self.fill_stats["processing_time"] = processing_time
        
        print(f"=" * 60)
        print(f"📊 PROCESSING COMPLETE")
        print(f"✅ Successfully processed: {success_count}/{len(files)} files")
        print(f"📈 Total gaps filled: {self.fill_stats['total_gaps_filled']:,} bars")
        print(f"⏱️  Processing time: {processing_time:.1f} seconds")
        print(f"💾 Fixed files saved to: {self.fixed_dir}")
        
        return results
    
    def compare_before_after(self, symbol: str) -> None:
        """Compare original vs fixed data for a symbol"""
        original_file = os.path.join(self.raw_dir, f"GEN_{symbol}_M1_1month.csv")
        fixed_file = os.path.join(self.fixed_dir, f"GEN_{symbol}_M1_1month_fixed.csv")
        
        if not os.path.exists(original_file) or not os.path.exists(fixed_file):
            print(f"❌ Cannot compare {symbol} - files missing")
            return
        
        df_orig = pd.read_csv(original_file)
        df_fixed = pd.read_csv(fixed_file)
        
        # Detect gaps in original
        gaps_orig = self.detect_gaps(df_orig)
        
        print(f"📊 COMPARISON: {symbol}")
        print(f"=" * 40)
        print(f"Original records: {len(df_orig):,}")
        print(f"Fixed records: {len(df_fixed):,}")
        print(f"Bars added: {len(df_fixed) - len(df_orig):,}")
        print(f"Original gaps: {len(gaps_orig)}")
        print(f"Data completeness: {len(df_fixed) / (len(df_fixed) + len(gaps_orig)) * 100:.1f}%")

def main():
    """Main execution function with strategy selection"""
    
    print("🎯 DATA GAP FILLER - Strategy Selection")
    print("=" * 60)
    print("Available Strategies:")
    print("1. forward_fill  - Conservative (carry previous values)")
    print("2. linear       - Smooth transitions (interpolate)")
    print("3. flat         - Constant prices (no movement)")
    print("4. smart        - Hybrid approach (recommended)")
    print("=" * 60)
    
    # Initialize gap filler
    filler = DataGapFiller()
    
    # Process problematic symbols with smart strategy
    problem_symbols = ["USOUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCNH"]
    
    print("🎯 Processing problematic symbols with SMART strategy:")
    results = filler.process_all_files(strategy="smart", symbols=problem_symbols)
    
    # Show comparison for worst case
    if "USOUSD" in results and results["USOUSD"]:
        print(f"\n📈 BEFORE/AFTER COMPARISON:")
        filler.compare_before_after("USOUSD")

if __name__ == "__main__":
    main()
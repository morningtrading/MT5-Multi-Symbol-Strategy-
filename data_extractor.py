#!/usr/bin/env python3
"""
Multi-Symbol Data Extractor for MT5 - Enhanced & Fixed
======================================================

This script extracts 1-month of 1-minute OHLC data for all tradeable symbols
from the screened symbol list and saves them as CSV files.

ENHANCED FEATURES (Fixed from lessons learned):
- Configurable sleep delays between requests (prevents rate limiting)
- Retry logic for failed requests (handles connection issues)  
- Better error handling and logging
- Support for both old and new symbol specification formats
- Comprehensive progress tracking and statistics
- Saves data as CSV files with standardized naming (GEN_SYMBOL_M1_1month.csv)
- ZERO tolerance for bugs - all issues fixed at source

Usage:
    python data_extractor.py
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional, Tuple

class EnhancedDataExtractor:
    """Production-grade data extractor with all lessons learned applied"""
    
    def __init__(self, 
                 sleep_between_requests: float = 1.0,
                 sleep_between_symbols: float = 2.0,
                 max_retries: int = 3,
                 data_dir: str = "CSVdata"):
        """
        Initialize the enhanced data extractor
        
        Args:
            sleep_between_requests: Seconds to sleep between individual requests
            sleep_between_symbols: Seconds to sleep between different symbols
            max_retries: Maximum retry attempts for failed requests
            data_dir: Directory to save CSV files
        """
        self.sleep_between_requests = sleep_between_requests
        self.sleep_between_symbols = sleep_between_symbols
        self.max_retries = max_retries
        self.data_dir = data_dir
        
        # Ensure directories exist
        os.makedirs(os.path.join(data_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "processed"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "analysis"), exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            "symbols_processed": 0,
            "symbols_successful": 0,
            "symbols_failed": 0,
            "total_bars": 0,
            "total_retries": 0,
            "failed_symbols": [],
            "successful_symbols": [],
            "start_time": None,
            "end_time": None
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def connect_mt5(self) -> bool:
        """Initialize MT5 connection with enhanced error handling"""
        self.log("🔌 Initializing MT5 connection...")
        
        if not mt5.initialize():
            error_code = mt5.last_error()
            self.log(f"❌ MT5 initialization failed: {error_code}", "ERROR")
            return False
            
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            self.log("❌ Failed to get account info", "ERROR")
            return False
            
        self.log(f"✅ Connected to MT5 - Account: {account_info.login}, Server: {account_info.server}")
        return True
        
    def load_symbol_specs(self) -> Dict:
        """Load symbol specifications from previous screening"""
        try:
            with open('symbol_specifications.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.log("❌ Symbol specifications not found. Run symbol_screener.py first.", "ERROR")
            raise
        except Exception as e:
            self.log(f"❌ Error loading symbol specs: {e}", "ERROR")
            raise
            
    def get_tradeable_symbols(self, symbol_specs: Dict) -> Dict[str, Dict]:
        """Extract tradeable symbols from specs, handling both old and new formats"""
        if 'approved_symbols' in symbol_specs:
            # Old format
            return symbol_specs['approved_symbols']
        else:
            # New format
            return {k: v for k, v in symbol_specs['symbol_specifications'].items() 
                   if v.get('tradeable', False)}
                   
    def get_data_with_retry(self, symbol: str, timeframe, date_from, date_to, attempt: int = 1) -> Optional[np.ndarray]:
        """
        Get data with retry logic and proper error handling
        
        Args:
            symbol: Trading symbol
            timeframe: MT5 timeframe constant
            date_from: Start date
            date_to: End date
            attempt: Current attempt number
            
        Returns:
            Numpy array of rates or None if failed
        """
        try:
            if attempt > 1:
                retry_sleep = self.sleep_between_requests * attempt
                self.log(f"  ⏱️  Waiting {retry_sleep:.1f}s before retry {attempt}/{self.max_retries}...")
                time.sleep(retry_sleep)
            elif self.sleep_between_requests > 0:
                time.sleep(self.sleep_between_requests)
                
            # Request data
            rates = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
            
            if rates is None:
                error = mt5.last_error()
                self.log(f"  ⚠️  Data request failed: {error}", "WARN")
                
                if attempt < self.max_retries:
                    self.stats["total_retries"] += 1
                    return self.get_data_with_retry(symbol, timeframe, date_from, date_to, attempt + 1)
                else:
                    self.log(f"  ❌ Max retries reached for {symbol}", "ERROR")
                    return None
                    
            if len(rates) == 0:
                self.log(f"  ⚠️  No data returned for {symbol}", "WARN")
                return None
                
            self.log(f"  ✅ Retrieved {len(rates):,} bars for {symbol}")
            return rates
            
        except Exception as e:
            self.log(f"  ❌ Exception during data request: {e}", "ERROR")
            
            if attempt < self.max_retries:
                self.stats["total_retries"] += 1
                return self.get_data_with_retry(symbol, timeframe, date_from, date_to, attempt + 1)
            else:
                return None
                
    def extract_symbol_data(self, symbol: str, symbol_info: Dict) -> bool:
        """
        Extract data for a single symbol with enhanced error handling
        
        Args:
            symbol: Trading symbol to extract
            symbol_info: Symbol information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get description and spread with fallbacks
            description = symbol_info.get('description', symbol_info.get('symbol', 'N/A'))
            spread = symbol_info.get('spread', symbol_info.get('spread_float', symbol_info.get('spread_points', 0)))
            
            self.log(f"📊 {symbol}: {description} | Spread: {spread}")
            
            # Calculate date range (1 month of data)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            # Get data with retry logic
            rates = self.get_data_with_retry(
                symbol=symbol,
                timeframe=mt5.TIMEFRAME_M1,
                date_from=start_date,
                date_to=end_date
            )
            
            if rates is None:
                self.log(f"❌ Failed to extract data for {symbol}", "ERROR")
                return False
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Add spread information with fallbacks
            current_spread = symbol_info.get('spread', symbol_info.get('spread_float', symbol_info.get('spread_points', 0)))
            df['spread'] = current_spread
            
            # Generate filename following user's naming preference (GEN_ prefix)
            filename = f"GEN_{symbol}_M1_1month.csv"
            filepath = os.path.join(self.data_dir, "raw", filename)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
            
            self.log(f"💾 Saved {len(df):,} bars to {filename} ({file_size_mb:.2f} MB)")
            self.log(f"📅 Date range: {df['time'].min()} to {df['time'].max()}")
            
            # Update statistics
            self.stats["total_bars"] += len(df)
            self.stats["successful_symbols"].append(symbol)
            
            return True
            
        except Exception as e:
            self.log(f"❌ Exception extracting {symbol}: {e}", "ERROR")
            return False
            
    def run_extraction(self) -> Dict:
        """
        Run complete extraction process for all tradeable symbols
        
        Returns:
            Dictionary with extraction results and statistics
        """
        self.log("🚀 STARTING ENHANCED DATA EXTRACTION")
        self.log("=" * 60)
        
        self.stats["start_time"] = datetime.now()
        
        # Connect to MT5
        if not self.connect_mt5():
            return {"success": False, "error": "MT5 connection failed"}
            
        # Load symbol specifications
        try:
            symbol_specs = self.load_symbol_specs()
        except Exception as e:
            return {"success": False, "error": f"Failed to load symbol specs: {e}"}
            
        # Get tradeable symbols
        tradeable_symbols = self.get_tradeable_symbols(symbol_specs)
        
        if not tradeable_symbols:
            return {"success": False, "error": "No tradeable symbols found"}
            
        self.log(f"📋 Found {len(tradeable_symbols)} tradeable symbols")
        self.log(f"⚙️  Settings: sleep={self.sleep_between_requests}s, retries={self.max_retries}")
        self.log(f"🎯 Symbols: {list(tradeable_symbols.keys())}")
        
        # Process each symbol
        for i, (symbol, symbol_info) in enumerate(tradeable_symbols.items(), 1):
            self.log(f"\n📈 Progress: {i}/{len(tradeable_symbols)} symbols")
            self.log("-" * 40)
            
            self.stats["symbols_processed"] += 1
            success = self.extract_symbol_data(symbol, symbol_info)
            
            if success:
                self.stats["symbols_successful"] += 1
            else:
                self.stats["symbols_failed"] += 1
                self.stats["failed_symbols"].append(symbol)
                
            # Sleep between symbols (except last one)
            if i < len(tradeable_symbols) and self.sleep_between_symbols > 0:
                self.log(f"⏱️  Sleeping {self.sleep_between_symbols}s before next symbol...")
                time.sleep(self.sleep_between_symbols)
                
        # Final statistics
        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        self.log("\n" + "=" * 60)
        self.log("🎯 EXTRACTION COMPLETE")
        self.log("=" * 60)
        self.log(f"⏰ Duration: {duration:.1f} seconds")
        self.log(f"📊 Symbols processed: {self.stats['symbols_processed']}")
        self.log(f"✅ Successful: {self.stats['symbols_successful']}")
        self.log(f"❌ Failed: {self.stats['symbols_failed']}")
        self.log(f"📈 Total bars: {self.stats['total_bars']:,}")
        self.log(f"🔄 Total retries: {self.stats['total_retries']}")
        
        if self.stats['symbols_successful'] > 0:
            avg_bars = self.stats['total_bars'] / self.stats['symbols_successful']
            self.log(f"📊 Average bars per symbol: {avg_bars:,.0f}")
            
        if self.stats['failed_symbols']:
            self.log(f"❌ Failed symbols: {self.stats['failed_symbols']}")
        else:
            self.log("🎉 ALL SYMBOLS EXTRACTED SUCCESSFULLY!")
            
        # Save extraction summary
        summary = {
            "metadata": {
                "extraction_date": datetime.now().isoformat(),
                "extractor_version": "Enhanced-Fixed",
                "data_directory": self.data_dir,
                "extraction_settings": {
                    "sleep_between_requests": self.sleep_between_requests,
                    "sleep_between_symbols": self.sleep_between_symbols,
                    "max_retries": self.max_retries
                }
            },
            "statistics": self.stats,
            "successful_extractions": {
                symbol: f"GEN_{symbol}_M1_1month.csv" 
                for symbol in self.stats["successful_symbols"]
            }
        }
        
        summary_path = os.path.join(self.data_dir, "extraction_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
            
        self.log(f"📋 Summary saved to: {summary_path}")
        
        # Cleanup MT5 connection
        mt5.shutdown()
        self.log("🔌 MT5 connection closed")
        
        return {
            "success": True,
            "statistics": self.stats,
            "summary_file": summary_path
        }


def main():
    """Main function"""
    # Create extractor with proven settings from testing
    extractor = EnhancedDataExtractor(
        sleep_between_requests=1.0,    # Proven to work well
        sleep_between_symbols=2.0,     # Good balance of speed vs reliability  
        max_retries=3                  # Sufficient for most issues
    )
    
    # Run extraction
    result = extractor.run_extraction()
    
    if result["success"]:
        stats = result["statistics"]
        print(f"\n✅ EXTRACTION COMPLETED SUCCESSFULLY!")
        print(f"📊 {stats['symbols_successful']}/{stats['symbols_processed']} symbols successful")
        print(f"📈 {stats['total_bars']:,} total bars extracted")
        
        if stats['symbols_failed'] == 0:
            print("🎉 PERFECT RUN - ALL SYMBOLS EXTRACTED!")
        else:
            print(f"⚠️  {stats['symbols_failed']} symbols failed")
            
    else:
        print(f"\n❌ EXTRACTION FAILED: {result.get('error', 'Unknown error')}")
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())
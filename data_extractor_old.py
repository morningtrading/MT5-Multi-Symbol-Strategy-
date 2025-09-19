#!/usr/bin/env python3
"""
Multi-Symbol CSV Data Extractor
===============================
Download 1-month historical data for all validated MT5 symbols.
Optimized for speed with progress tracking and compact reporting.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-19
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
import concurrent.futures
from pathlib import Path

@dataclass
class ExtractionResult:
    """Result of data extraction for a single symbol"""
    symbol: str
    success: bool
    records: int
    file_path: str
    file_size: float  # MB
    duration: float  # seconds
    error_message: str = ""
    date_range: tuple = None

class MultiSymbolDataExtractor:
    """High-speed data extraction for multiple symbols"""
    
    def __init__(self, config_file: str = "symbol_specifications.json"):
        self.config_file = config_file
        self.symbols_config = {}
        self.tradeable_symbols = []
        self.results = {}
        self.total_records = 0
        self.total_size_mb = 0.0
        
        # Configuration
        self.output_dir = "CSVdata"
        self.timeframe = mt5.TIMEFRAME_M1  # 1-minute bars
        self.days_back = 30  # 1 month
        self.max_workers = 3  # Parallel downloads
        
        # Timeframe mapping
        self.timeframe_map = {
            mt5.TIMEFRAME_M1: "M1",
            mt5.TIMEFRAME_M5: "M5", 
            mt5.TIMEFRAME_M15: "M15",
            mt5.TIMEFRAME_M30: "M30",
            mt5.TIMEFRAME_H1: "H1",
            mt5.TIMEFRAME_H4: "H4",
            mt5.TIMEFRAME_D1: "D1"
        }
    
    def load_validated_symbols(self) -> bool:
        """Load validated symbols from screening results"""
        try:
            if not os.path.exists(self.config_file):
                print(f"❌ Config file not found: {self.config_file}")
                print("💡 Run symbol_screener.py first to generate symbol specifications")
                return False
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.symbols_config = config.get('symbol_specifications', {})
            self.tradeable_symbols = config.get('tradeable_symbols', [])
            
            if not self.tradeable_symbols:
                print("❌ No tradeable symbols found in configuration")
                return False
            
            print(f"📋 Loaded {len(self.tradeable_symbols)} tradeable symbols")
            print(f"🎯 Symbols: {', '.join(self.tradeable_symbols)}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading symbol config: {e}")
            return False
    
    def setup_output_directory(self) -> bool:
        """Create output directory structure"""
        try:
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different purposes
            subdirs = ['raw', 'processed', 'analysis']
            for subdir in subdirs:
                Path(self.output_dir, subdir).mkdir(exist_ok=True)
            
            print(f"📁 Output directory ready: {self.output_dir}/")
            return True
            
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            return False
    
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                print(f"❌ MT5 initialization failed: {error}")
                return False
            
            account = mt5.account_info()
            if not account:
                print("❌ No MT5 account information available")
                return False
            
            print(f"✅ MT5 Connected - Account: {account.login}")
            return True
            
        except Exception as e:
            print(f"💥 MT5 connection error: {e}")
            return False
    
    def extract_single_symbol(self, symbol: str) -> ExtractionResult:
        """Extract data for a single symbol with detailed progress"""
        start_time = time.time()
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.days_back)
            
            # Check symbol availability
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                return ExtractionResult(
                    symbol=symbol, success=False, records=0, file_path="", 
                    file_size=0, duration=time.time() - start_time,
                    error_message="Symbol not found"
                )
            
            # Make symbol visible if needed
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    return ExtractionResult(
                        symbol=symbol, success=False, records=0, file_path="", 
                        file_size=0, duration=time.time() - start_time,
                        error_message="Cannot enable symbol"
                    )
            
            # Extract data
            rates = mt5.copy_rates_range(symbol, self.timeframe, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                error = mt5.last_error()
                return ExtractionResult(
                    symbol=symbol, success=False, records=0, file_path="", 
                    file_size=0, duration=time.time() - start_time,
                    error_message=f"No data retrieved: {error}"
                )
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['datetime'] = pd.to_datetime(df['time'], unit='s')
            
            # Reorder columns for better readability
            df = df[['datetime', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']]
            
            # Generate filename following naming convention
            timeframe_str = self.timeframe_map.get(self.timeframe, "M1")
            filename = f"GEN_{symbol}_{timeframe_str}_1month.csv"
            file_path = os.path.join(self.output_dir, 'raw', filename)
            
            # Save to CSV
            df.to_csv(file_path, index=False)
            
            # Calculate file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            
            # Get actual date range from data
            actual_start = df['datetime'].min()
            actual_end = df['datetime'].max()
            
            return ExtractionResult(
                symbol=symbol, success=True, records=len(df), file_path=file_path,
                file_size=file_size_mb, duration=time.time() - start_time,
                date_range=(actual_start, actual_end)
            )
            
        except Exception as e:
            return ExtractionResult(
                symbol=symbol, success=False, records=0, file_path="",
                file_size=0, duration=time.time() - start_time,
                error_message=f"Exception: {str(e)}"
            )
    
    def extract_all_symbols(self) -> Dict[str, ExtractionResult]:
        """Extract data for all symbols with progress tracking"""
        if not self.tradeable_symbols:
            print("❌ No symbols to extract")
            return {}
        
        print("🚀 MULTI-SYMBOL DATA EXTRACTION")
        print("=" * 60)
        print(f"📊 Extracting {len(self.tradeable_symbols)} symbols")
        print(f"📅 Date range: {self.days_back} days back from now")
        print(f"⏱️  Timeframe: {self.timeframe_map.get(self.timeframe, 'M1')}")
        print(f"📁 Output: {self.output_dir}/raw/")
        print("-" * 60)
        
        results = {}
        successful_count = 0
        
        for i, symbol in enumerate(self.tradeable_symbols, 1):
            print(f"Extracting {symbol:<10} ({i:2}/{len(self.tradeable_symbols)})...", end=" ", flush=True)
            
            result = self.extract_single_symbol(symbol)
            results[symbol] = result
            
            if result.success:
                successful_count += 1
                self.total_records += result.records
                self.total_size_mb += result.file_size
                
                # Status with file info
                print(f"✅ {result.records:,} bars | {result.file_size:.1f}MB | {result.duration:.1f}s")
            else:
                print(f"❌ {result.error_message}")
            
            # Small delay to avoid overwhelming MT5
            time.sleep(0.1)
        
        self.results = results
        
        # Summary
        print("-" * 60)
        print(f"📊 EXTRACTION COMPLETE")
        print(f"✅ Successful: {successful_count}/{len(self.tradeable_symbols)}")
        print(f"📈 Total records: {self.total_records:,}")
        print(f"💾 Total size: {self.total_size_mb:.1f}MB")
        print("=" * 60)
        
        return results
    
    def generate_extraction_report(self) -> str:
        """Generate comprehensive one-line extraction report"""
        if not self.results:
            return "⏳ No extraction completed yet"
        
        successful = len([r for r in self.results.values() if r.success])
        failed = len([r for r in self.results.values() if not r.success])
        
        # Get account info
        account_info = mt5.account_info()
        account_str = f"Account #{account_info.login}" if account_info else "Unknown Account"
        
        # Successful symbols
        success_symbols = [symbol for symbol, result in self.results.items() if result.success]
        success_str = ', '.join(success_symbols) if success_symbols else "None"
        
        # Failed symbols with reasons
        failed_list = []
        for symbol, result in self.results.items():
            if not result.success:
                failed_list.append(f"{symbol}({result.error_message})")
        
        failed_str = ', '.join(failed_list) if failed_list else "None"
        
        return (f"📊 {account_str} | Extracted: {self.days_back}d data | "
                f"✅ Success: {successful} [{success_str}] | "
                f"❌ Failed: {failed} [{failed_str}] | "
                f"📈 {self.total_records:,} bars | 💾 {self.total_size_mb:.1f}MB")
    
    def save_extraction_summary(self, filename: str = "extraction_summary.json") -> bool:
        """Save detailed extraction summary to JSON"""
        try:
            summary_data = {
                "metadata": {
                    "extraction_date": datetime.now().isoformat(),
                    "timeframe": self.timeframe_map.get(self.timeframe, "M1"),
                    "days_back": self.days_back,
                    "output_directory": self.output_dir
                },
                "account_info": {},
                "extraction_stats": {
                    "total_symbols_requested": len(self.tradeable_symbols),
                    "successful_extractions": len([r for r in self.results.values() if r.success]),
                    "failed_extractions": len([r for r in self.results.values() if not r.success]),
                    "total_records": self.total_records,
                    "total_size_mb": round(self.total_size_mb, 2)
                },
                "symbol_results": {}
            }
            
            # Add account info
            account_info = mt5.account_info()
            if account_info:
                summary_data["account_info"] = {
                    "login": account_info.login,
                    "balance": account_info.balance,
                    "server": getattr(account_info, 'server', 'Unknown'),
                    "company": getattr(account_info, 'company', 'Unknown')
                }
            
            # Add individual symbol results
            for symbol, result in self.results.items():
                summary_data["symbol_results"][symbol] = {
                    "success": result.success,
                    "records": result.records,
                    "file_path": result.file_path,
                    "file_size_mb": round(result.file_size, 2),
                    "duration_seconds": round(result.duration, 2),
                    "error_message": result.error_message,
                    "date_range_start": result.date_range[0].isoformat() if result.date_range else None,
                    "date_range_end": result.date_range[1].isoformat() if result.date_range else None
                }
            
            # Save to file
            summary_path = os.path.join(self.output_dir, filename)
            with open(summary_path, 'w') as f:
                json.dump(summary_data, f, indent=2, default=str)
            
            print(f"💾 Extraction summary saved: {summary_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving extraction summary: {e}")
            return False
    
    def get_successful_files(self) -> List[str]:
        """Get list of successfully created CSV files"""
        return [result.file_path for result in self.results.values() if result.success]
    
    def cleanup(self):
        """Cleanup MT5 connection"""
        try:
            mt5.shutdown()
        except:
            pass

def main():
    """Main execution function"""
    print("🚀 MULTI-SYMBOL DATA EXTRACTOR")
    print("=" * 60)
    
    # Initialize extractor
    extractor = MultiSymbolDataExtractor()
    
    try:
        # Load validated symbols
        if not extractor.load_validated_symbols():
            return
        
        # Setup output directory
        if not extractor.setup_output_directory():
            return
        
        # Initialize MT5
        if not extractor.initialize_mt5():
            return
        
        # Extract data for all symbols
        results = extractor.extract_all_symbols()
        
        if not results:
            print("❌ No data extracted")
            return
        
        # Save summary
        extractor.save_extraction_summary()
        
        # Generate final report
        print("\n" + "=" * 80)
        print("📋 COMPREHENSIVE EXTRACTION SUMMARY")
        print("=" * 80)
        print(extractor.generate_extraction_report())
        print("=" * 80)
        
        # Show successful files
        successful_files = extractor.get_successful_files()
        if successful_files:
            print(f"\n📁 Created {len(successful_files)} CSV files:")
            for file_path in successful_files:
                filename = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   • {filename} ({file_size:.1f}MB)")
        
    finally:
        # Cleanup
        extractor.cleanup()
        print("\n✅ Data extraction complete!")

if __name__ == "__main__":
    main()
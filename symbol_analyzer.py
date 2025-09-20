#!/usr/bin/env python3
"""
Unified Symbol Analyzer - Multi-Symbol Strategy Framework
========================================================

Comprehensive symbol analysis system combining:
- Symbol Discovery: Find all available MT5 symbols and match against target list
- Symbol Screening: Complete specification retrieval and validation
- Data Quality Control: Analyze downloaded CSV data for integrity issues

This unified module provides all symbol analysis functionality in one place
with shared MT5 connection handling and consistent logging.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: 1.0 (Unified)
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# SHARED DATA CLASSES
# ============================================================================

@dataclass
class QualityIssue:
    """Represents a data quality issue"""
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    location: str  # row number, date range, etc.
    impact: str    # potential impact on trading
    recommendation: str

@dataclass
class SymbolQualityReport:
    """Quality report for a single symbol"""
    symbol: str
    file_path: str
    file_size_mb: float
    total_records: int
    date_range: tuple
    
    # Quality metrics
    completeness_score: float    # % of expected data present
    consistency_score: float     # consistency of OHLC data
    timeliness_score: float     # proper time sequencing
    accuracy_score: float       # data value reasonableness
    overall_quality_score: float
    
    # Detailed findings
    time_gaps: List[dict]
    data_anomalies: List[dict]
    ohlc_violations: List[dict]
    volume_issues: List[dict]
    spread_issues: List[dict]
    
    # Issues summary
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    total_issues: int
    
    quality_grade: str  # A, B, C, D, F

@dataclass
class SymbolSpecification:
    """Complete MT5 symbol specification"""
    # Basic Info
    symbol: str
    available: bool
    tradeable: bool
    visible: bool
    
    # Trading Specifications
    tick_size: float
    tick_value: float
    contract_size: float
    min_lot: float
    max_lot: float
    lot_step: float
    
    # Pricing Info
    spread_points: int
    spread_float: float
    current_bid: float
    current_ask: float
    
    # Currency Info
    currency_base: str
    currency_profit: str
    currency_margin: str
    
    # Trading Permissions
    trade_mode: int
    trade_mode_description: str
    execution_mode: int
    
    # Market Hours
    sessions_quotes: str
    sessions_trades: str
    
    # Additional Info
    digits: int
    point: float
    margin_initial: float
    margin_maintenance: float
    
    # Status
    last_updated: str
    error_message: str = ""
    data_quality_score: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

# ============================================================================
# SYMBOL DISCOVERY CLASS
# ============================================================================

class SymbolDiscoverer:
    """MT5 Symbol Discovery - Find and match symbols against target lists"""
    
    def __init__(self):
        """Initialize symbol discoverer"""
        self.target_symbols = [
            "AUDUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "NZDUSD", "SOLUSD", 
            "US2000", "US30", "US500", "USDCAD", "USDCHF", "USDCNH", "USDJPY", 
            "USDSEK", "USO.NYSE", "USTEC", "XAUUSD", "XRPUSD"
        ]
        self.discovery_results = {}
    
    def discover_all_symbols(self) -> Dict:
        """Discover all symbols available in MT5 and match against targets"""
        print("🔍 MT5 SYMBOL DISCOVERY")
        print("=" * 50)
        
        # Get all symbols
        all_symbols = mt5.symbols_get()
        if not all_symbols:
            print("❌ No symbols found")
            return {}
        
        print(f"📊 Found {len(all_symbols)} total symbols in MT5")
        
        print("\n🎯 SYMBOL MATCHING")
        print("-" * 50)
        
        # Find exact matches
        available_symbols = [s.name for s in all_symbols]
        exact_matches = []
        partial_matches = {}
        
        for target in self.target_symbols:
            if target in available_symbols:
                exact_matches.append(target)
                print(f"✅ {target:<12} - Exact match")
            else:
                # Look for partial matches
                matches = [s for s in available_symbols if target.replace('.NYSE', '') in s or s in target]
                if matches:
                    partial_matches[target] = matches
                    print(f"🔍 {target:<12} - Possible matches: {matches[:3]}")
                else:
                    print(f"❌ {target:<12} - No matches found")
        
        print(f"\n📈 DISCOVERY SUMMARY")
        print("-" * 50)
        print(f"✅ Exact matches: {len(exact_matches)}")
        print(f"🔍 Partial matches: {len(partial_matches)}")
        print(f"❌ Not found: {len(self.target_symbols) - len(exact_matches) - len(partial_matches)}")
        
        if exact_matches:
            print(f"\n✅ Ready for trading: {', '.join(exact_matches)}")
        
        # Show popular symbols by category
        self._show_popular_symbols(all_symbols)
        
        # Store results
        self.discovery_results = {
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "popular_forex": self._get_forex_symbols(all_symbols),
            "popular_crypto": self._get_crypto_symbols(all_symbols),
            "popular_indices": self._get_index_symbols(all_symbols),
            "total_available": len(all_symbols),
            "discovery_time": datetime.now().isoformat()
        }
        
        return self.discovery_results
    
    def _show_popular_symbols(self, all_symbols):
        """Display popular symbols by category"""
        print(f"\n🌟 POPULAR SYMBOLS AVAILABLE:")
        print("-" * 50)
        
        forex_symbols = self._get_forex_symbols(all_symbols)
        crypto_symbols = self._get_crypto_symbols(all_symbols)
        index_symbols = self._get_index_symbols(all_symbols)
        
        if forex_symbols:
            print(f"💱 Forex: {', '.join(forex_symbols)}")
        if crypto_symbols:
            print(f"₿ Crypto: {', '.join(crypto_symbols)}")
        if index_symbols:
            print(f"📊 Indices: {', '.join(index_symbols)}")
    
    def _get_forex_symbols(self, all_symbols) -> List[str]:
        """Extract popular forex symbols"""
        return [s.name for s in all_symbols 
                if any(curr in s.name for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD']) 
                and len(s.name) == 6][:10]
    
    def _get_crypto_symbols(self, all_symbols) -> List[str]:
        """Extract popular crypto symbols"""
        return [s.name for s in all_symbols 
                if any(crypto in s.name for crypto in ['BTC', 'ETH', 'XRP', 'SOL']) 
                and 'USD' in s.name][:5]
    
    def _get_index_symbols(self, all_symbols) -> List[str]:
        """Extract popular index symbols"""
        return [s.name for s in all_symbols 
                if any(idx in s.name for idx in ['NAS', 'SPX', 'SP500', 'DOW', 'US30', 'US500'])][:5]
    
    def save_discovery_results(self, filename: str = "mt5_symbol_discovery.json") -> bool:
        """Save discovery results to JSON file"""
        if not self.discovery_results:
            return False
        
        try:
            with open(filename, "w") as f:
                json.dump(self.discovery_results, f, indent=2)
            
            print(f"\n💾 Discovery results saved to: {filename}")
            return True
        except Exception as e:
            print(f"❌ Failed to save discovery results: {e}")
            return False

# ============================================================================
# SYMBOL SCREENER CLASS
# ============================================================================

class SymbolScreener:
    """MT5 Symbol Screener - Complete specification retrieval and validation"""
    
    def __init__(self, symbol_list_file: str = "list_symbols_capitalpoint.csv"):
        self.symbol_list_file = symbol_list_file
        self.symbols_raw = []
        self.symbol_specs = {}
        self.screening_stats = {
            "total_symbols": 0,
            "available_symbols": 0,
            "tradeable_symbols": 0,
            "failed_symbols": 0,
            "screening_time": 0.0,
            "last_screening": None
        }
    
    def load_symbol_list(self) -> List[str]:
        """Load symbols from CSV file"""
        try:
            if not os.path.exists(self.symbol_list_file):
                print(f"❌ Symbol list file not found: {self.symbol_list_file}")
                return []
            
            with open(self.symbol_list_file, 'r') as f:
                content = f.read().strip()
                # Handle both comma-separated and line-separated formats
                if ',' in content:
                    symbols = [s.strip() for s in content.split(',')]
                else:
                    symbols = [s.strip() for s in content.split('\n') if s.strip()]
            
            self.symbols_raw = [s for s in symbols if s]  # Remove empty strings
            print(f"📋 Loaded {len(self.symbols_raw)} symbols: {', '.join(self.symbols_raw[:5])}...")
            return self.symbols_raw
            
        except Exception as e:
            print(f"❌ Error loading symbol list: {e}")
            return []
    
    def get_complete_symbol_spec(self, symbol: str) -> SymbolSpecification:
        """Get complete specification for a single symbol"""
        try:
            # Get basic symbol info
            symbol_info = mt5.symbol_info(symbol)
            
            if symbol_info is None:
                return SymbolSpecification(
                    symbol=symbol, available=False, tradeable=False, visible=False,
                    tick_size=0, tick_value=0, contract_size=0, min_lot=0, max_lot=0, lot_step=0,
                    spread_points=0, spread_float=0, current_bid=0, current_ask=0,
                    currency_base="", currency_profit="", currency_margin="",
                    trade_mode=0, trade_mode_description="DISABLED", execution_mode=0,
                    sessions_quotes="", sessions_trades="", digits=0, point=0,
                    margin_initial=0, margin_maintenance=0, last_updated=datetime.now().isoformat(),
                    error_message="Symbol not found in MT5"
                )
            
            # Try to make symbol visible if not already
            if not symbol_info.visible:
                mt5.symbol_select(symbol, True)
                # Refresh symbol info
                symbol_info = mt5.symbol_info(symbol)
            
            # Get current tick data
            tick = mt5.symbol_info_tick(symbol)
            current_bid = tick.bid if tick else 0.0
            current_ask = tick.ask if tick else 0.0
            
            # Determine trading status
            available = symbol_info is not None
            tradeable = symbol_info.trade_mode in [
                mt5.SYMBOL_TRADE_MODE_FULL,
                mt5.SYMBOL_TRADE_MODE_CLOSEONLY
            ] if symbol_info else False
            
            # Get trade mode description
            trade_mode_descriptions = {
                0: "DISABLED",
                1: "LONGONLY", 
                2: "SHORTONLY",
                3: "CLOSEONLY",
                4: "FULL"
            }
            
            # Calculate data quality score
            data_quality = self.calculate_data_quality(symbol_info, tick)
            
            return SymbolSpecification(
                # Basic Info
                symbol=symbol,
                available=available,
                tradeable=tradeable,
                visible=symbol_info.visible,
                
                # Trading Specifications
                tick_size=symbol_info.point,
                tick_value=symbol_info.trade_tick_value,
                contract_size=symbol_info.trade_contract_size,
                min_lot=symbol_info.volume_min,
                max_lot=symbol_info.volume_max,
                lot_step=symbol_info.volume_step,
                
                # Pricing Info
                spread_points=symbol_info.spread,
                spread_float=symbol_info.spread * symbol_info.point,
                current_bid=current_bid,
                current_ask=current_ask,
                
                # Currency Info
                currency_base=symbol_info.currency_base,
                currency_profit=symbol_info.currency_profit,
                currency_margin=symbol_info.currency_margin,
                
                # Trading Permissions
                trade_mode=symbol_info.trade_mode,
                trade_mode_description=trade_mode_descriptions.get(symbol_info.trade_mode, "UNKNOWN"),
                execution_mode=getattr(symbol_info, 'execution_mode', 0),
                
                # Market Hours (simplified)
                sessions_quotes=str(getattr(symbol_info, 'sessions_quotes', '')) if symbol_info else "",
                sessions_trades=str(getattr(symbol_info, 'sessions_trades', '')) if symbol_info else "",
                
                # Additional Info
                digits=symbol_info.digits,
                point=symbol_info.point,
                margin_initial=getattr(symbol_info, 'margin_initial', 0),
                margin_maintenance=getattr(symbol_info, 'margin_maintenance', 0),
                
                # Status
                last_updated=datetime.now().isoformat(),
                data_quality_score=data_quality
            )
            
        except Exception as e:
            return SymbolSpecification(
                symbol=symbol, available=False, tradeable=False, visible=False,
                tick_size=0, tick_value=0, contract_size=0, min_lot=0, max_lot=0, lot_step=0,
                spread_points=0, spread_float=0, current_bid=0, current_ask=0,
                currency_base="", currency_profit="", currency_margin="",
                trade_mode=0, trade_mode_description="ERROR", execution_mode=0,
                sessions_quotes="", sessions_trades="", digits=0, point=0,
                margin_initial=0, margin_maintenance=0, last_updated=datetime.now().isoformat(),
                error_message=f"Exception: {str(e)}", data_quality_score=0.0
            )
    
    def calculate_data_quality(self, symbol_info, tick) -> float:
        """Calculate data quality score (0-100)"""
        score = 0.0
        
        # Basic availability (40 points)
        if symbol_info:
            score += 20
            if symbol_info.visible:
                score += 10
            if symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                score += 10
        
        # Tick data availability (30 points)
        if tick:
            score += 15
            if tick.bid > 0 and tick.ask > 0:
                score += 10
            if abs(tick.ask - tick.bid) > 0:  # Valid spread
                score += 5
        
        # Complete specifications (30 points)
        if symbol_info:
            if symbol_info.trade_tick_value > 0:
                score += 10
            if symbol_info.volume_min > 0:
                score += 10
            if symbol_info.currency_base and symbol_info.currency_profit:
                score += 10
        
        return score
    
    def screen_all_symbols(self) -> Dict[str, SymbolSpecification]:
        """Screen all symbols and get complete specifications"""
        if not self.symbols_raw:
            self.load_symbol_list()
        
        if not self.symbols_raw:
            print("❌ No symbols to screen")
            return {}
        
        print("🔍 COMPREHENSIVE SYMBOL SCREENING")
        print("=" * 60)
        
        start_time = time.time()
        results = {}
        
        for i, symbol in enumerate(self.symbols_raw):
            print(f"Scanning {symbol:<12} ({i+1:2}/{len(self.symbols_raw)})...", end=" ")
            
            spec = self.get_complete_symbol_spec(symbol)
            results[symbol] = spec
            
            # Status reporting
            if spec.tradeable:
                quality_icon = "🟢" if spec.data_quality_score >= 80 else "🟡" if spec.data_quality_score >= 60 else "🔴"
                print(f"✅ Tradeable {quality_icon} (Quality: {spec.data_quality_score:.0f}%)")
            elif spec.available:
                print(f"⚠️  Available only (not tradeable)")
            else:
                print(f"❌ Not available - {spec.error_message}")
            
            # Small delay to avoid overwhelming MT5
            time.sleep(0.1)
        
        screening_time = time.time() - start_time
        
        # Update statistics
        self.screening_stats.update({
            "total_symbols": len(results),
            "available_symbols": len([s for s in results.values() if s.available]),
            "tradeable_symbols": len([s for s in results.values() if s.tradeable]),
            "failed_symbols": len([s for s in results.values() if not s.available]),
            "screening_time": screening_time,
            "last_screening": datetime.now().isoformat()
        })
        
        self.symbol_specs = results
        
        # Summary report
        print("=" * 60)
        print(f"📊 SCREENING COMPLETE ({screening_time:.1f}s)")
        print(f"📈 Available: {self.screening_stats['available_symbols']}/{self.screening_stats['total_symbols']}")
        print(f"💹 Tradeable: {self.screening_stats['tradeable_symbols']}/{self.screening_stats['total_symbols']}")
        print(f"❌ Failed: {self.screening_stats['failed_symbols']}/{self.screening_stats['total_symbols']}")
        
        return results
    
    def classify_symbol_type(self, symbol: str) -> str:
        """Classify symbol into trading categories"""
        forex_majors = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY"]
        forex_minors = ["USDSEK", "USDCNH"]
        crypto = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"]
        indices = ["US2000", "US30", "US500", "USTEC"]
        
        if symbol in forex_majors:
            return "forex_major"
        elif symbol in forex_minors:
            return "forex_minor"
        elif symbol in crypto:
            return "cryptocurrency"
        elif symbol == "XAUUSD":
            return "precious_metal"
        elif symbol == "USO.NYSE":
            return "commodity"
        elif symbol in indices:
            return "index"
        else:
            return "other"
    
    def export_symbol_config(self, filename: str = "symbol_specifications.json") -> bool:
        """Export complete symbol specifications to JSON config file"""
        if not self.symbol_specs:
            print("❌ No symbol specifications to export")
            return False
        
        try:
            # Prepare export data
            export_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "source_file": self.symbol_list_file,
                    "mt5_connection": "active",
                    "screening_stats": self.screening_stats
                },
                "symbol_groups": self.create_symbol_groups(),
                "symbol_specifications": {},
                "tradeable_symbols": [],
                "available_symbols": [],
                "summary": {
                    "total_symbols": len(self.symbol_specs),
                    "tradeable_count": 0,
                    "available_count": 0,
                    "avg_quality_score": 0.0
                }
            }
            
            # Add individual symbol specifications
            quality_scores = []
            for symbol, spec in self.symbol_specs.items():
                export_data["symbol_specifications"][symbol] = {
                    **spec.to_dict(),
                    "symbol_type": self.classify_symbol_type(symbol)
                }
                
                if spec.available:
                    export_data["available_symbols"].append(symbol)
                
                if spec.tradeable:
                    export_data["tradeable_symbols"].append(symbol)
                
                if spec.data_quality_score > 0:
                    quality_scores.append(spec.data_quality_score)
            
            # Update summary statistics
            export_data["summary"].update({
                "tradeable_count": len(export_data["tradeable_symbols"]),
                "available_count": len(export_data["available_symbols"]),
                "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            })
            
            # Write to JSON file
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"💾 Symbol specifications exported to: {filename}")
            print(f"📊 Exported {len(export_data['tradeable_symbols'])} tradeable symbols")
            
            return True
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def create_symbol_groups(self) -> Dict[str, List[str]]:
        """Create trading groups based on symbol types"""
        groups = {}
        
        for symbol, spec in self.symbol_specs.items():
            if not spec.tradeable:
                continue
                
            symbol_type = self.classify_symbol_type(symbol)
            
            if symbol_type not in groups:
                groups[symbol_type] = []
            
            groups[symbol_type].append(symbol)
        
        return groups
    
    def get_tradeable_symbols(self) -> List[str]:
        """Get list of tradeable symbols only"""
        return [symbol for symbol, spec in self.symbol_specs.items() if spec.tradeable]
    
    def get_high_quality_symbols(self, min_quality: float = 80.0) -> List[str]:
        """Get symbols with high data quality scores"""
        return [symbol for symbol, spec in self.symbol_specs.items() 
                if spec.tradeable and spec.data_quality_score >= min_quality]
    
    def generate_screening_summary(self, account_info=None) -> str:
        """Generate comprehensive screening summary"""
        if not self.symbol_specs:
            return "⏳ No screening completed yet"
        
        # Basic stats
        total_from_csv = len(self.symbols_raw)
        available_count = len([s for s in self.symbol_specs.values() if s.available])
        tradeable_count = len([s for s in self.symbol_specs.values() if s.tradeable])
        
        # Account info
        account_str = "Unknown Account"
        if account_info:
            account_str = f"Account #{account_info.login}"
            if hasattr(account_info, 'company') and account_info.company:
                account_str += f" ({account_info.company})"
            elif hasattr(account_info, 'server') and account_info.server:
                account_str += f" ({account_info.server})"
        
        # Approved symbols
        tradeable_symbols = [s for s, spec in self.symbol_specs.items() if spec.tradeable]
        approved_str = ', '.join(tradeable_symbols) if tradeable_symbols else "None"
        
        # Rejected symbols with reasons
        rejected_symbols = []
        for symbol, spec in self.symbol_specs.items():
            if not spec.tradeable:
                if not spec.available:
                    reason = "Not found in MT5"
                elif spec.trade_mode_description == "DISABLED":
                    reason = "Trading disabled"
                else:
                    reason = "Not tradeable"
                rejected_symbols.append(f"{symbol}({reason})")
        
        rejected_str = ', '.join(rejected_symbols) if rejected_symbols else "None"
        
        return (f"📊 CSV: {total_from_csv} symbols | {account_str} | "
                f"✅ OK: {tradeable_count} [{approved_str}] | "
                f"❌ Rejected: {len(rejected_symbols)} [{rejected_str}]")

# ============================================================================
# DATA QUALITY CONTROLLER CLASS
# ============================================================================

class DataQualityController:
    """Comprehensive data quality analysis system for CSV files"""
    
    def __init__(self, data_dir: str = "CSVdata"):
        self.data_dir = data_dir
        self.raw_data_dir = os.path.join(data_dir, "raw")
        self.quality_reports = {}
        self.summary_stats = {
            "files_analyzed": 0,
            "total_records": 0,
            "total_issues": 0,
            "avg_quality_score": 0.0,
            "analysis_duration": 0.0
        }
        
        # Quality thresholds
        self.thresholds = {
            "max_gap_minutes": 5,      # Max acceptable gap between bars
            "max_spread_ratio": 0.1,   # Max spread as % of price
            "min_volume": 1,           # Minimum tick volume
            "max_price_change": 0.2,   # Max % price change between bars
            "ohlc_tolerance": 0.0001   # OHLC relationship tolerance
        }
    
    def analyze_all_files(self) -> Dict[str, SymbolQualityReport]:
        """Analyze all CSV files in the raw data directory"""
        print("🔍 DATA QUALITY CONTROLLER")
        print("=" * 60)
        
        if not os.path.exists(self.raw_data_dir):
            print(f"❌ Raw data directory not found: {self.raw_data_dir}")
            return {}
        
        csv_files = [f for f in os.listdir(self.raw_data_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"❌ No CSV files found in {self.raw_data_dir}")
            return {}
        
        print(f"📊 Analyzing {len(csv_files)} CSV files")
        print("-" * 60)
        
        start_time = time.time()
        reports = {}
        
        for i, filename in enumerate(csv_files, 1):
            symbol = self.extract_symbol_from_filename(filename)
            print(f"Analyzing {symbol:<10} ({i:2}/{len(csv_files)})...", end=" ", flush=True)
            
            file_path = os.path.join(self.raw_data_dir, filename)
            report = self.analyze_single_file(file_path, symbol)
            
            if report:
                reports[symbol] = report
                grade_color = self.get_grade_color(report.quality_grade)
                print(f"{grade_color} Grade: {report.quality_grade} | Issues: {report.total_issues} | Score: {report.overall_quality_score:.1f}%")
            else:
                print("❌ Analysis failed")
        
        self.quality_reports = reports
        
        # Update summary stats
        analysis_time = time.time() - start_time
        self.summary_stats.update({
            "files_analyzed": len(reports),
            "total_records": sum(r.total_records for r in reports.values()),
            "total_issues": sum(r.total_issues for r in reports.values()),
            "avg_quality_score": sum(r.overall_quality_score for r in reports.values()) / len(reports) if reports else 0,
            "analysis_duration": analysis_time
        })
        
        print("-" * 60)
        print(f"📊 ANALYSIS COMPLETE ({analysis_time:.1f}s)")
        print(f"📈 Files: {len(reports)} | Records: {self.summary_stats['total_records']:,}")
        print(f"⚠️  Total Issues: {self.summary_stats['total_issues']} | Avg Score: {self.summary_stats['avg_quality_score']:.1f}%")
        print("=" * 60)
        
        return reports
    
    def analyze_single_file(self, file_path: str, symbol: str) -> Optional[SymbolQualityReport]:
        """Analyze a single CSV file for quality issues"""
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Basic file info
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            total_records = len(df)
            
            # Convert datetime column (handle both 'time' and 'datetime' column names)
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'])
            elif 'time' in df.columns:
                df['datetime'] = pd.to_datetime(df['time'])
            else:
                # Try to find a datetime-like column
                datetime_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
                if datetime_cols:
                    df['datetime'] = pd.to_datetime(df[datetime_cols[0]])
                else:
                    raise ValueError("No datetime column found")
            
            date_range = (df['datetime'].min(), df['datetime'].max())
            
            # Initialize quality checks
            time_gaps = self.check_time_gaps(df)
            data_anomalies = self.check_data_anomalies(df)
            ohlc_violations = self.check_ohlc_integrity(df)
            volume_issues = self.check_volume_data(df)
            spread_issues = self.check_spread_data(df)
            
            # Calculate quality scores
            completeness_score = self.calculate_completeness_score(df, time_gaps)
            consistency_score = self.calculate_consistency_score(ohlc_violations, data_anomalies)
            timeliness_score = self.calculate_timeliness_score(time_gaps)
            accuracy_score = self.calculate_accuracy_score(data_anomalies, volume_issues, spread_issues)
            
            # Overall quality score (weighted average)
            overall_quality_score = (
                completeness_score * 0.3 +
                consistency_score * 0.25 +
                timeliness_score * 0.25 +
                accuracy_score * 0.2
            )
            
            # Count issues by severity
            all_issues = time_gaps + data_anomalies + ohlc_violations + volume_issues + spread_issues
            critical_issues = len([i for i in all_issues if i.get('severity') == 'critical'])
            high_issues = len([i for i in all_issues if i.get('severity') == 'high'])
            medium_issues = len([i for i in all_issues if i.get('severity') == 'medium'])
            low_issues = len([i for i in all_issues if i.get('severity') == 'low'])
            total_issues = len(all_issues)
            
            # Assign quality grade
            quality_grade = self.assign_quality_grade(overall_quality_score, critical_issues, high_issues)
            
            return SymbolQualityReport(
                symbol=symbol,
                file_path=file_path,
                file_size_mb=file_size_mb,
                total_records=total_records,
                date_range=date_range,
                completeness_score=completeness_score,
                consistency_score=consistency_score,
                timeliness_score=timeliness_score,
                accuracy_score=accuracy_score,
                overall_quality_score=overall_quality_score,
                time_gaps=time_gaps,
                data_anomalies=data_anomalies,
                ohlc_violations=ohlc_violations,
                volume_issues=volume_issues,
                spread_issues=spread_issues,
                critical_issues=critical_issues,
                high_issues=high_issues,
                medium_issues=medium_issues,
                low_issues=low_issues,
                total_issues=total_issues,
                quality_grade=quality_grade
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return None
    
    def check_time_gaps(self, df: pd.DataFrame) -> List[dict]:
        """Check for time gaps in the data"""
        gaps = []
        df_sorted = df.sort_values('datetime')
        
        # Calculate time differences
        time_diffs = df_sorted['datetime'].diff()
        
        # Expected 1-minute intervals
        expected_interval = timedelta(minutes=1)
        tolerance = timedelta(seconds=30)
        
        for i, diff in enumerate(time_diffs[1:], 1):
            if diff > expected_interval + tolerance:
                gap_minutes = diff.total_seconds() / 60
                severity = 'critical' if gap_minutes > 60 else 'high' if gap_minutes > 15 else 'medium'
                
                gaps.append({
                    'issue_type': 'time_gap',
                    'severity': severity,
                    'description': f'{gap_minutes:.1f} minute gap in data',
                    'location': f'Row {i}, after {df_sorted.iloc[i-1]["datetime"]}',
                    'gap_size_minutes': gap_minutes,
                    'start_time': df_sorted.iloc[i-1]['datetime'],
                    'end_time': df_sorted.iloc[i]['datetime']
                })
        
        return gaps
    
    def check_ohlc_integrity(self, df: pd.DataFrame) -> List[dict]:
        """Check OHLC data integrity"""
        violations = []
        
        for i, row in df.iterrows():
            open_price, high, low, close = row['open'], row['high'], row['low'], row['close']
            
            # Check if high is actually the highest
            if high < max(open_price, close) - self.thresholds['ohlc_tolerance']:
                violations.append({
                    'issue_type': 'ohlc_violation',
                    'severity': 'high',
                    'description': 'High price lower than open/close',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
            
            # Check if low is actually the lowest
            if low > min(open_price, close) + self.thresholds['ohlc_tolerance']:
                violations.append({
                    'issue_type': 'ohlc_violation',
                    'severity': 'high',
                    'description': 'Low price higher than open/close',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
            
            # Check for zero or negative prices
            if any(price <= 0 for price in [open_price, high, low, close]):
                violations.append({
                    'issue_type': 'invalid_price',
                    'severity': 'critical',
                    'description': 'Zero or negative price detected',
                    'location': f'Row {i}, {row["datetime"]}',
                    'values': f'O:{open_price:.2f} H:{high:.2f} L:{low:.2f} C:{close:.2f}'
                })
        
        return violations
    
    def check_data_anomalies(self, df: pd.DataFrame) -> List[dict]:
        """Check for data anomalies and outliers"""
        anomalies = []
        
        # Sort by datetime
        df_sorted = df.sort_values('datetime').copy()
        
        # Calculate price changes
        df_sorted['price_change'] = df_sorted['close'].pct_change()
        
        # Check for extreme price movements
        for i, row in df_sorted.iterrows():
            if pd.isna(row['price_change']):
                continue
                
            if abs(row['price_change']) > self.thresholds['max_price_change']:
                severity = 'critical' if abs(row['price_change']) > 0.5 else 'high'
                anomalies.append({
                    'issue_type': 'extreme_price_change',
                    'severity': severity,
                    'description': f'Extreme price change: {row["price_change"]:.2%}',
                    'location': f'Row {i}, {row["datetime"]}',
                    'price_change_pct': row['price_change'] * 100
                })
        
        # Check for duplicate timestamps
        duplicates = df_sorted[df_sorted['datetime'].duplicated()]
        for i, row in duplicates.iterrows():
            anomalies.append({
                'issue_type': 'duplicate_timestamp',
                'severity': 'medium',
                'description': 'Duplicate timestamp found',
                'location': f'Row {i}, {row["datetime"]}',
                'timestamp': row['datetime']
            })
        
        return anomalies
    
    def check_volume_data(self, df: pd.DataFrame) -> List[dict]:
        """Check volume data quality"""
        issues = []
        
        for i, row in df.iterrows():
            # Check for zero or missing volume
            if pd.isna(row['tick_volume']) or row['tick_volume'] < self.thresholds['min_volume']:
                issues.append({
                    'issue_type': 'low_volume',
                    'severity': 'low',
                    'description': f'Low/zero tick volume: {row["tick_volume"]}',
                    'location': f'Row {i}, {row["datetime"]}',
                    'volume': row['tick_volume']
                })
        
        return issues
    
    def check_spread_data(self, df: pd.DataFrame) -> List[dict]:
        """Check spread data reasonableness"""
        issues = []
        
        for i, row in df.iterrows():
            # Calculate spread as percentage of price
            if row['close'] > 0:
                spread_pct = (row['spread'] * 0.01) / row['close']  # Assuming spread is in points
                
                if spread_pct > self.thresholds['max_spread_ratio']:
                    issues.append({
                        'issue_type': 'excessive_spread',
                        'severity': 'medium',
                        'description': f'Excessive spread: {spread_pct:.3%} of price',
                        'location': f'Row {i}, {row["datetime"]}',
                        'spread_points': row['spread'],
                        'spread_percentage': spread_pct * 100
                    })
        
        return issues
    
    def calculate_completeness_score(self, df: pd.DataFrame, time_gaps: List[dict]) -> float:
        """Calculate data completeness score"""
        if not time_gaps:
            return 100.0
        
        # Calculate total gap time
        total_gap_minutes = sum(gap['gap_size_minutes'] for gap in time_gaps)
        
        # Calculate expected total time
        time_span_minutes = (df['datetime'].max() - df['datetime'].min()).total_seconds() / 60
        
        # Completeness = (total_time - gaps) / total_time
        completeness = max(0, (time_span_minutes - total_gap_minutes) / time_span_minutes)
        return completeness * 100
    
    def calculate_consistency_score(self, ohlc_violations: List[dict], anomalies: List[dict]) -> float:
        """Calculate data consistency score"""
        total_violations = len(ohlc_violations) + len(anomalies)
        
        if total_violations == 0:
            return 100.0
        
        # Penalty based on violation count (logarithmic scale)
        penalty = min(100, total_violations * 5 + np.log(total_violations + 1) * 10)
        return max(0, 100 - penalty)
    
    def calculate_timeliness_score(self, time_gaps: List[dict]) -> float:
        """Calculate timeliness score based on gaps"""
        if not time_gaps:
            return 100.0
        
        # Weight gaps by severity
        penalty = 0
        for gap in time_gaps:
            if gap['severity'] == 'critical':
                penalty += 20
            elif gap['severity'] == 'high':
                penalty += 10
            elif gap['severity'] == 'medium':
                penalty += 5
            else:
                penalty += 2
        
        return max(0, 100 - penalty)
    
    def calculate_accuracy_score(self, anomalies: List[dict], volume_issues: List[dict], spread_issues: List[dict]) -> float:
        """Calculate accuracy score"""
        total_issues = len(anomalies) + len(volume_issues) + len(spread_issues)
        
        if total_issues == 0:
            return 100.0
        
        # Penalty based on issue count and severity
        penalty = min(100, total_issues * 3)
        return max(0, 100 - penalty)
    
    def assign_quality_grade(self, overall_score: float, critical_issues: int, high_issues: int) -> str:
        """Assign quality grade based on score and issues"""
        if critical_issues > 0:
            return 'F'
        elif high_issues > 5:
            return 'D'
        elif overall_score >= 90:
            return 'A'
        elif overall_score >= 80:
            return 'B'
        elif overall_score >= 70:
            return 'C'
        elif overall_score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_grade_color(self, grade: str) -> str:
        """Get colored output for grade"""
        colors = {
            'A': '🟢',
            'B': '🟡', 
            'C': '🟠',
            'D': '🔴',
            'F': '💀'
        }
        return colors.get(grade, '⚪')
    
    def extract_symbol_from_filename(self, filename: str) -> str:
        """Extract symbol from filename like GEN_BTCUSD_M1_1month.csv"""
        parts = filename.replace('.csv', '').split('_')
        if len(parts) >= 2 and parts[0] == 'GEN':
            return parts[1]
        return filename.replace('.csv', '')
    
    def generate_quality_summary(self) -> str:
        """Generate comprehensive quality summary"""
        if not self.quality_reports:
            return "⏳ No quality analysis completed yet"
        
        # Grade distribution
        grade_counts = {}
        for report in self.quality_reports.values():
            grade = report.quality_grade
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Critical symbols (grade D or F)
        critical_symbols = [symbol for symbol, report in self.quality_reports.items() 
                          if report.quality_grade in ['D', 'F']]
        
        # Top quality symbols (grade A)
        excellent_symbols = [symbol for symbol, report in self.quality_reports.items() 
                           if report.quality_grade == 'A']
        
        grade_dist = ' | '.join([f"{grade}:{count}" for grade, count in sorted(grade_counts.items())])
        excellent_str = ', '.join(excellent_symbols) if excellent_symbols else "None"
        critical_str = ', '.join(critical_symbols) if critical_symbols else "None"
        
        return (f"📊 Quality Control | Files: {self.summary_stats['files_analyzed']} | "
                f"Records: {self.summary_stats['total_records']:,} | "
                f"Avg Score: {self.summary_stats['avg_quality_score']:.1f}% | "
                f"Grades: [{grade_dist}] | "
                f"🟢 Excellent: [{excellent_str}] | "
                f"🔴 Issues: [{critical_str}] | "
                f"⚡ {self.summary_stats['analysis_duration']:.1f}s")
    
    def save_quality_report(self, filename: str = "data_quality_report.json") -> bool:
        """Save detailed quality report to JSON"""
        try:
            report_data = {
                "metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "analyzer_version": "1.0",
                    "data_directory": self.data_dir
                },
                "summary_statistics": self.summary_stats,
                "quality_thresholds": self.thresholds,
                "symbol_reports": {}
            }
            
            # Convert reports to serializable format
            for symbol, report in self.quality_reports.items():
                report_dict = asdict(report)
                # Convert datetime objects to strings
                if report_dict['date_range']:
                    report_dict['date_range'] = [
                        report_dict['date_range'][0].isoformat(),
                        report_dict['date_range'][1].isoformat()
                    ]
                report_data["symbol_reports"][symbol] = report_dict
            
            # Save to file
            output_path = os.path.join(self.data_dir, filename)
            with open(output_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            print(f"💾 Quality report saved: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving quality report: {e}")
            return False

# ============================================================================
# UNIFIED SYMBOL ANALYZER CLASS
# ============================================================================

class SymbolAnalyzer:
    """
    Unified Symbol Analyzer - Complete symbol analysis system
    
    Combines discovery, screening, and quality control in a single interface
    with shared MT5 connection and consistent logging.
    """
    
    def __init__(self, symbol_list_file: str = "list_symbols_capitalpoint.csv", 
                 data_dir: str = "CSVdata"):
        """Initialize unified symbol analyzer"""
        self.symbol_list_file = symbol_list_file
        self.data_dir = data_dir
        
        # Initialize components
        self.discoverer = SymbolDiscoverer()
        self.screener = SymbolScreener(symbol_list_file)
        self.quality_controller = DataQualityController(data_dir)
        
        # Shared state
        self.mt5_connected = False
        self.account_info = None
        self.analysis_results = {
            "discovery": {},
            "screening": {},
            "quality": {}
        }
    
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection with comprehensive error handling"""
        try:
            if not mt5.initialize():
                error = mt5.last_error()
                print(f"❌ MT5 initialization failed: {error}")
                return False
            
            # Verify connection
            account = mt5.account_info()
            if not account:
                print("❌ No MT5 account information available")
                return False
            
            self.account_info = account
            self.mt5_connected = True
            
            print(f"✅ MT5 Connected - Account: {account.login} | Balance: ${account.balance:.2f}")
            return True
            
        except Exception as e:
            print(f"💥 MT5 connection error: {e}")
            return False
    
    def shutdown_mt5(self):
        """Safely shutdown MT5 connection"""
        if self.mt5_connected:
            mt5.shutdown()
            self.mt5_connected = False
            print("✅ MT5 connection closed")
    
    def discover_symbols(self) -> Dict:
        """Run symbol discovery"""
        if not self.mt5_connected:
            if not self.initialize_mt5():
                return {}
        
        results = self.discoverer.discover_all_symbols()
        self.analysis_results["discovery"] = results
        
        # Save results
        self.discoverer.save_discovery_results()
        
        return results
    
    def screen_symbols(self) -> Dict[str, SymbolSpecification]:
        """Run comprehensive symbol screening"""
        if not self.mt5_connected:
            if not self.initialize_mt5():
                return {}
        
        results = self.screener.screen_all_symbols()
        self.analysis_results["screening"] = results
        
        # Export specifications
        self.screener.export_symbol_config()
        
        return results
    
    def analyze_data_quality(self) -> Dict[str, SymbolQualityReport]:
        """Run data quality analysis"""
        results = self.quality_controller.analyze_all_files()
        self.analysis_results["quality"] = results
        
        # Save quality report
        self.quality_controller.save_quality_report()
        
        return results
    
    def run_complete_analysis(self) -> Dict:
        """Run all analysis components in sequence"""
        print("🚀 UNIFIED SYMBOL ANALYZER")
        print("=" * 80)
        print("Running complete symbol analysis pipeline...")
        print("=" * 80)
        
        start_time = time.time()
        
        # Initialize MT5
        if not self.initialize_mt5():
            print("❌ Cannot proceed without MT5 connection")
            return {}
        
        try:
            # Step 1: Symbol Discovery
            print("\n" + "=" * 40)
            print("STEP 1: SYMBOL DISCOVERY")
            print("=" * 40)
            discovery_results = self.discover_symbols()
            
            # Step 2: Symbol Screening
            print("\n" + "=" * 40)
            print("STEP 2: SYMBOL SCREENING")
            print("=" * 40)
            screening_results = self.screen_symbols()
            
            # Step 3: Data Quality Analysis (if CSV data exists)
            print("\n" + "=" * 40)
            print("STEP 3: DATA QUALITY ANALYSIS")
            print("=" * 40)
            quality_results = self.analyze_data_quality()
            
            # Generate comprehensive summary
            total_time = time.time() - start_time
            self.print_unified_summary(total_time)
            
            return {
                "discovery": discovery_results,
                "screening": screening_results,
                "quality": quality_results,
                "analysis_time": total_time,
                "timestamp": datetime.now().isoformat()
            }
        
        finally:
            self.shutdown_mt5()
    
    def print_unified_summary(self, analysis_time: float):
        """Print comprehensive analysis summary"""
        print("\n" + "=" * 80)
        print("📋 UNIFIED ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Discovery summary
        if self.analysis_results["discovery"]:
            discovery = self.analysis_results["discovery"]
            print(f"🔍 Discovery: {discovery.get('total_available', 0)} total symbols | "
                  f"{len(discovery.get('exact_matches', []))} exact matches")
        
        # Screening summary
        if self.analysis_results["screening"]:
            screening = self.analysis_results["screening"]
            tradeable_count = len([s for s in screening.values() if s.tradeable])
            print(f"📊 Screening: {len(screening)} screened | {tradeable_count} tradeable")
        
        # Quality summary
        if self.analysis_results["quality"]:
            quality = self.analysis_results["quality"]
            avg_score = sum(r.overall_quality_score for r in quality.values()) / len(quality) if quality else 0
            print(f"🔬 Quality: {len(quality)} files analyzed | Avg score: {avg_score:.1f}%")
        
        print(f"⏱️  Total Analysis Time: {analysis_time:.1f} seconds")
        print("=" * 80)
        
        # Account information
        if self.account_info:
            print(f"🏦 Account: {self.account_info.login} | Balance: ${self.account_info.balance:.2f}")
        
        print("✅ Unified symbol analysis complete!")

# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def run_discovery():
    """Run symbol discovery only"""
    analyzer = SymbolAnalyzer()
    if analyzer.initialize_mt5():
        try:
            analyzer.discover_symbols()
        finally:
            analyzer.shutdown_mt5()

def run_screening():
    """Run symbol screening only"""
    analyzer = SymbolAnalyzer()
    if analyzer.initialize_mt5():
        try:
            analyzer.screen_symbols()
        finally:
            analyzer.shutdown_mt5()

def run_quality_analysis():
    """Run data quality analysis only"""
    analyzer = SymbolAnalyzer()
    analyzer.analyze_data_quality()

def main():
    """Main function - run complete analysis pipeline"""
    analyzer = SymbolAnalyzer()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    # Allow running individual components via command line
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "discover":
            run_discovery()
        elif command == "screen":
            run_screening()
        elif command == "quality":
            run_quality_analysis()
        else:
            print("Usage: python symbol_analyzer.py [discover|screen|quality]")
            print("Or run without arguments for complete analysis")
    else:
        main()
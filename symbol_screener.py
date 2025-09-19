#!/usr/bin/env python3
"""
MT5 Symbol Screener - Multi-Symbol Strategy
============================================
Complete symbol screening and specification retrieval for MT5 trading.
Validates symbol availability and extracts all trading specifications.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-19
"""

import MetaTrader5 as mt5
import pandas as pd
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import os

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

class MT5SymbolScreener:
    """Complete MT5 symbol screening and specification system"""
    
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
        
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection with error handling"""
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
            
            print(f"✅ MT5 Connected - Account: {account.login} | Balance: ${account.balance:.2f}")
            return True
            
        except Exception as e:
            print(f"💥 MT5 connection error: {e}")
            return False
    
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
    
    def generate_compact_report(self) -> str:
        """Generate one-line status report"""
        if not self.symbol_specs:
            return "⏳ No screening completed yet"
        
        total = len(self.symbol_specs)
        tradeable = len(self.get_tradeable_symbols())
        high_quality = len(self.get_high_quality_symbols())
        
        return f"🔍 Symbols: {total} total | {tradeable} tradeable | {high_quality} high-quality | ⚡{self.screening_stats['screening_time']:.1f}s"
    
    def generate_comprehensive_summary(self, account_info=None) -> str:
        """Generate comprehensive one-line summary with account and rejection details"""
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

def main():
    """Main function for standalone execution"""
    print("🚀 MT5 SYMBOL SCREENER")
    print("=" * 50)
    
    # Initialize screener
    screener = MT5SymbolScreener()
    
    # Initialize MT5
    if not screener.initialize_mt5():
        print("❌ Cannot proceed without MT5 connection")
        return
    
    # Get account info for summary
    account_info = mt5.account_info()
    
    # Load and screen symbols
    symbols = screener.load_symbol_list()
    if not symbols:
        print("❌ No symbols to process")
        return
    
    # Complete screening
    results = screener.screen_all_symbols()
    
    # Export configuration
    if screener.export_symbol_config():
        print("✅ Configuration file created successfully")
    
    # Generate comprehensive summary
    print("\n" + "=" * 80)
    print("📋 COMPREHENSIVE SUMMARY")
    print("=" * 80)
    print(screener.generate_comprehensive_summary(account_info))
    print("=" * 80)
    
    # Cleanup
    mt5.shutdown()
    print("\n✅ Symbol screening complete!")

if __name__ == "__main__":
    main()

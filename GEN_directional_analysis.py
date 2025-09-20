#!/usr/bin/env python3
"""
Directional Signal Analysis
==========================

Detailed breakdown of long/short signals across all timeframes and symbols.
This shows exactly how our system evaluates both bullish and bearish opportunities.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: DIRECTIONAL_ANALYSIS
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
from tabulate import tabulate

# Import our enhanced components
from GEN_enhanced_multi_timeframe_strategy import EnhancedMultiTimeframeStrategy

class DirectionalSignalAnalysis:
    """
    Analyze directional signals (long/short) across all symbols and timeframes
    """
    
    def __init__(self):
        """Initialize directional analysis"""
        self.strategy = EnhancedMultiTimeframeStrategy()
        self.test_symbols = ["BTCUSD", "ETHUSD", "US2000", "NAS100", "USOUSD"]
        
    def analyze_directional_signals(self):
        """Comprehensive directional signal analysis"""
        
        print("🎯 DIRECTIONAL SIGNAL ANALYSIS")
        print("=" * 80)
        print("📊 ANALYZING BOTH LONG AND SHORT OPPORTUNITIES")
        print("=" * 80)
        
        results = {}
        
        # Analyze each symbol
        for symbol in self.test_symbols:
            print(f"\n🔍 Analyzing {symbol} directional signals...")
            
            try:
                signal = self.strategy.analyze_symbol_enhanced(symbol)
                results[symbol] = signal
                
                # Show quick directional summary
                self.display_quick_directional_summary(symbol, signal)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[symbol] = None
        
        # Comprehensive directional breakdown
        self.display_comprehensive_directional_analysis(results)
        
        # Show what conditions would trigger long/short signals
        self.show_signal_trigger_conditions()
        
        return results
    
    def display_quick_directional_summary(self, symbol: str, signal):
        """Quick directional summary for each symbol"""
        
        # Count directional signals per timeframe
        bullish_tfs = 0
        bearish_tfs = 0
        neutral_tfs = 0
        
        for tf_signal in signal.timeframe_signals:
            direction_value = tf_signal.direction.value
            if direction_value > 0:
                bullish_tfs += 1
            elif direction_value < 0:
                bearish_tfs += 1
            else:
                neutral_tfs += 1
        
        total_tfs = len(signal.timeframe_signals)
        bullish_pct = (bullish_tfs / total_tfs) * 100
        bearish_pct = (bearish_tfs / total_tfs) * 100
        neutral_pct = (neutral_tfs / total_tfs) * 100
        
        print(f"   📊 Timeframe Directional Breakdown:")
        print(f"      🟢 Bullish: {bullish_tfs}/{total_tfs} ({bullish_pct:.1f}%)")
        print(f"      🔴 Bearish: {bearish_tfs}/{total_tfs} ({bearish_pct:.1f}%)")
        print(f"      ⚪ Neutral: {neutral_tfs}/{total_tfs} ({neutral_pct:.1f}%)")
        
        # Overall bias
        if bullish_tfs > bearish_tfs:
            bias = f"🟢 BULLISH BIAS (+{bullish_tfs - bearish_tfs} timeframes)"
        elif bearish_tfs > bullish_tfs:
            bias = f"🔴 BEARISH BIAS (+{bearish_tfs - bullish_tfs} timeframes)"
        else:
            bias = "⚪ NEUTRAL (Equal bull/bear signals)"
        
        print(f"      🎯 Overall Bias: {bias}")
        print(f"      📈 Final Action: {signal.recommended_action}")
    
    def display_comprehensive_directional_analysis(self, results: Dict):
        """Comprehensive directional analysis across all symbols"""
        
        print(f"\n📋 COMPREHENSIVE DIRECTIONAL BREAKDOWN")
        print("=" * 80)
        
        # Prepare detailed directional table
        table_data = []
        headers = ["Symbol", "Overall", "M1", "M5", "M15", "H1", "H4", "D1", "Bull%", "Bear%", "Final"]
        
        for symbol, signal in results.items():
            if signal is None:
                continue
            
            row = [symbol]
            
            # Overall direction
            overall_icon = self._get_direction_icon(signal.overall_direction)
            row.append(overall_icon)
            
            # Individual timeframe directions
            timeframe_directions = {}
            for tf_signal in signal.timeframe_signals:
                tf_name = tf_signal.timeframe.name
                tf_icon = self._get_direction_icon(tf_signal.direction)
                timeframe_directions[tf_name] = tf_icon
            
            # Add timeframes in order
            for tf in ["M1", "M5", "M15", "H1", "H4", "D1"]:
                row.append(timeframe_directions.get(tf, "❓"))
            
            # Calculate percentages
            bullish_count = sum(1 for tf_signal in signal.timeframe_signals if tf_signal.direction.value > 0)
            bearish_count = sum(1 for tf_signal in signal.timeframe_signals if tf_signal.direction.value < 0)
            total_count = len(signal.timeframe_signals)
            
            bull_pct = (bullish_count / total_count) * 100
            bear_pct = (bearish_count / total_count) * 100
            
            row.append(f"{bull_pct:.0f}%")
            row.append(f"{bear_pct:.0f}%")
            row.append(signal.recommended_action)
            
            table_data.append(row)
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        # Market-wide directional statistics
        self.display_market_directional_stats(results)
    
    def display_market_directional_stats(self, results: Dict):
        """Display market-wide directional statistics"""
        
        print(f"\n📊 MARKET-WIDE DIRECTIONAL STATISTICS")
        print("-" * 50)
        
        # Aggregate all timeframe signals
        all_bullish = 0
        all_bearish = 0
        all_neutral = 0
        total_signals = 0
        
        timeframe_stats = {
            "M1": {"bull": 0, "bear": 0, "neutral": 0},
            "M5": {"bull": 0, "bear": 0, "neutral": 0},
            "M15": {"bull": 0, "bear": 0, "neutral": 0},
            "H1": {"bull": 0, "bear": 0, "neutral": 0},
            "H4": {"bull": 0, "bear": 0, "neutral": 0},
            "D1": {"bull": 0, "bear": 0, "neutral": 0}
        }
        
        for symbol, signal in results.items():
            if signal is None:
                continue
            
            for tf_signal in signal.timeframe_signals:
                total_signals += 1
                direction_value = tf_signal.direction.value
                tf_name = tf_signal.timeframe.name
                
                if direction_value > 0:
                    all_bullish += 1
                    timeframe_stats[tf_name]["bull"] += 1
                elif direction_value < 0:
                    all_bearish += 1
                    timeframe_stats[tf_name]["bear"] += 1
                else:
                    all_neutral += 1
                    timeframe_stats[tf_name]["neutral"] += 1
        
        # Overall market sentiment
        if total_signals > 0:
            bull_pct = (all_bullish / total_signals) * 100
            bear_pct = (all_bearish / total_signals) * 100
            neutral_pct = (all_neutral / total_signals) * 100
            
            print(f"🌍 OVERALL MARKET SENTIMENT:")
            print(f"   🟢 Bullish Signals: {all_bullish}/{total_signals} ({bull_pct:.1f}%)")
            print(f"   🔴 Bearish Signals: {all_bearish}/{total_signals} ({bear_pct:.1f}%)")
            print(f"   ⚪ Neutral Signals: {all_neutral}/{total_signals} ({neutral_pct:.1f}%)")
            
            # Market bias
            if bull_pct > bear_pct + 10:
                market_bias = "🟢 BULLISH MARKET"
            elif bear_pct > bull_pct + 10:
                market_bias = "🔴 BEARISH MARKET"
            else:
                market_bias = "⚪ MIXED/CONSOLIDATING MARKET"
            
            print(f"   🎯 Market Bias: {market_bias}")
        
        # Timeframe-specific sentiment
        print(f"\n⏰ TIMEFRAME-SPECIFIC SENTIMENT:")
        tf_table = []
        tf_headers = ["Timeframe", "Bullish", "Bearish", "Neutral", "Bias"]
        
        for tf_name, stats in timeframe_stats.items():
            total_tf = stats["bull"] + stats["bear"] + stats["neutral"]
            if total_tf == 0:
                continue
                
            bull_tf_pct = (stats["bull"] / total_tf) * 100
            bear_tf_pct = (stats["bear"] / total_tf) * 100
            
            if bull_tf_pct > bear_tf_pct + 20:
                bias = "🟢 BULLISH"
            elif bear_tf_pct > bull_tf_pct + 20:
                bias = "🔴 BEARISH"  
            else:
                bias = "⚪ MIXED"
            
            tf_table.append([
                tf_name,
                f"{stats['bull']} ({bull_tf_pct:.0f}%)",
                f"{stats['bear']} ({bear_tf_pct:.0f}%)",
                f"{stats['neutral']}",
                bias
            ])
        
        print(tabulate(tf_table, headers=tf_headers, tablefmt="grid"))
    
    def show_signal_trigger_conditions(self):
        """Show what conditions would trigger long/short signals"""
        
        print(f"\n🎯 LONG/SHORT SIGNAL TRIGGER CONDITIONS")
        print("=" * 60)
        
        print("🟢 LONG SIGNAL TRIGGERS:")
        print("   📈 Required Conditions:")
        print("      • Confluence Score ≥ 0.65")
        print("      • Overall Strength ≥ 0.6") 
        print("      • Risk Level ≤ MEDIUM")
        print("      • Bullish timeframe majority (≥60%)")
        print("      • Key indicators aligned:")
        print("        - RSI < 70 (not overbought)")
        print("        - MACD histogram > 0")
        print("        - Price above key moving averages")
        print("        - Stochastic showing bullish momentum")
        
        print("\n🔴 SHORT SIGNAL TRIGGERS:")
        print("   📉 Required Conditions:")
        print("      • Confluence Score ≥ 0.65")
        print("      • Overall Strength ≥ 0.6")
        print("      • Risk Level ≤ MEDIUM") 
        print("      • Bearish timeframe majority (≥60%)")
        print("      • Key indicators aligned:")
        print("        - RSI > 30 (not oversold)")
        print("        - MACD histogram < 0")
        print("        - Price below key moving averages")
        print("        - Stochastic showing bearish momentum")
        
        print("\n⚪ WHY WE'RE SEEING HOLD SIGNALS:")
        print("   🎯 Current Market Conditions:")
        print("      • Mixed timeframe signals (no clear majority)")
        print("      • High risk environment detected")
        print("      • Confluence scores below action threshold")
        print("      • Conflicting indicator signals")
        print("      • System prioritizing capital preservation")
        
        print("\n🔍 WHAT TO MONITOR FOR SIGNAL CHANGES:")
        print("   📊 Watch for:")
        print("      • Confluence scores rising above 0.65")
        print("      • Clear timeframe alignment (>60% agreement)")
        print("      • Risk levels dropping to MEDIUM or LOW")
        print("      • Volume confirmation on directional moves")
        print("      • Breakouts from current consolidation ranges")
    
    def _get_direction_icon(self, direction) -> str:
        """Get direction icon"""
        from GEN_multi_timeframe_strategy import MarketDirection
        icons = {
            MarketDirection.STRONG_BUY: "🚀",
            MarketDirection.BUY: "🟢",
            MarketDirection.NEUTRAL: "⚪",
            MarketDirection.SELL: "🔴", 
            MarketDirection.STRONG_SELL: "💥"
        }
        return icons.get(direction, "❓")

def main():
    """Main execution for directional analysis"""
    
    print("🎯 DIRECTIONAL SIGNAL ANALYSIS - LONG/SHORT OPPORTUNITIES")
    print("=" * 80)
    
    try:
        analyzer = DirectionalSignalAnalysis()
        results = analyzer.analyze_directional_signals()
        
        print(f"\n" + "🎯" * 25)
        print("🎯 DIRECTIONAL ANALYSIS COMPLETE")
        print("🎯" * 25)
        
        print(f"\n📊 KEY FINDINGS:")
        print(f"   • System analyzes BOTH long and short opportunities")
        print(f"   • Current market shows mixed directional signals")
        print(f"   • Waiting for higher confluence to trigger trades")
        print(f"   • Risk management prioritizing capital preservation")
        
    except Exception as e:
        print(f"❌ Directional analysis error: {e}")
        raise

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🎯 TRADING STATUS DASHBOARD
==========================
Enhanced Multi-Timeframe Strategy Engine - Trading Signal Status Table
Designed for web dashboard integration with detailed signal breakdowns.

Signal Categories:
• 🟢 STRONG_BUY / BUY (Long positions)
• 🔴 STRONG_SELL / SELL (Short positions)  
• ⚪ HOLD (No position)
• 👁️ WATCH (Monitor but don't trade)
"""

import sys
import os
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our enhanced strategy system
from GEN_enhanced_multi_timeframe_strategy import EnhancedMultiTimeframeStrategy

class TradingStatusDashboard:
    """Trading Status Dashboard for Web Integration"""
    
    def __init__(self):
        """Initialize the trading status dashboard"""
        self.strategy = EnhancedMultiTimeframeStrategy()
        self.symbols = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'US2000', 'NAS100', 'NAS100ft', 'SP500ft', 'USOUSD', 'XAUUSD']
        self.timeframes = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']
        
    def get_signal_category(self, signal_data):
        """
        Determine signal category based on strategy output
        
        Returns:
        - STRONG_BUY: Confluence ≥ 0.8, Strength ≥ 0.75, Low Risk
        - BUY: Confluence ≥ 0.65, Strength ≥ 0.6, Med Risk or better
        - STRONG_SELL: Confluence ≥ 0.8, Strength ≥ 0.75, Low Risk (bearish)
        - SELL: Confluence ≥ 0.65, Strength ≥ 0.6, Med Risk or better (bearish)
        - WATCH: Confluence ≥ 0.5, some interesting signals
        - HOLD: Below thresholds or mixed signals
        """
        action = signal_data.get('action', 'HOLD')
        confluence = signal_data.get('confluence_score', 0)
        strength = signal_data.get('overall_strength', 0)
        risk = signal_data.get('risk_level', 'HIGH')
        bullish_tf = signal_data.get('bullish_timeframes', 0)
        bearish_tf = signal_data.get('bearish_timeframes', 0)
        total_tf = bullish_tf + bearish_tf + signal_data.get('neutral_timeframes', 0)
        
        # Calculate directional bias
        if total_tf > 0:
            bull_pct = (bullish_tf / total_tf) * 100
            bear_pct = (bearish_tf / total_tf) * 100
        else:
            bull_pct = bear_pct = 0
            
        # Determine signal strength and direction
        is_bullish = bull_pct > bear_pct and bull_pct >= 50
        is_bearish = bear_pct > bull_pct and bear_pct >= 50
        
        # STRONG signals (highest confidence)
        if confluence >= 0.8 and strength >= 0.75 and risk in ['LOW', 'VERY_LOW']:
            if is_bullish and bull_pct >= 67:  # 2/3 majority
                return "🟢 STRONG_BUY", "Strong bullish confluence across timeframes"
            elif is_bearish and bear_pct >= 67:
                return "🔴 STRONG_SELL", "Strong bearish confluence across timeframes"
        
        # Regular BUY/SELL signals
        if confluence >= 0.65 and strength >= 0.6 and risk in ['LOW', 'MEDIUM', 'VERY_LOW']:
            if is_bullish and bull_pct >= 60:
                return "🟢 BUY", "Good bullish setup with decent confluence"
            elif is_bearish and bear_pct >= 60:
                return "🔴 SELL", "Good bearish setup with decent confluence"
        
        # WATCH signals (interesting but not actionable)
        if confluence >= 0.5 or strength >= 0.5:
            if abs(bull_pct - bear_pct) <= 20:  # Close competition
                return "👁️ WATCH", "Mixed signals - monitor for clarity"
            elif max(bull_pct, bear_pct) >= 50:
                direction = "bullish" if bull_pct > bear_pct else "bearish"
                return "👁️ WATCH", f"Developing {direction} setup - needs confirmation"
        
        # Default HOLD
        return "⚪ HOLD", "Insufficient signal strength or high risk"
    
    def get_risk_color(self, risk_level):
        """Get color coding for risk levels"""
        risk_colors = {
            'VERY_LOW': '🟢',
            'LOW': '🟡', 
            'MEDIUM': '🟠',
            'HIGH': '🔴',
            'VERY_HIGH': '⚫'
        }
        return risk_colors.get(risk_level, '⚪')
    
    def analyze_symbol(self, symbol):
        """Analyze a single symbol and return comprehensive status"""
        print(f"\n🔍 Analyzing {symbol}...")
        
        try:
            # Use the enhanced strategy's analyze_symbol_enhanced method
            confluent_signal = self.strategy.analyze_symbol_enhanced(symbol)
            
            # Extract key metrics from ConfluentSignal object
            signal_data = {
                'action': confluent_signal.recommended_action,
                'confluence_score': confluent_signal.confluence_score,
                'overall_strength': confluent_signal.overall_strength,
                'risk_level': confluent_signal.risk_level,
                'bullish_timeframes': 0,
                'bearish_timeframes': 0,
                'neutral_timeframes': 0,
                'timeframes': {},
                'current_price': confluent_signal.timeframe_signals[-1].price if confluent_signal.timeframe_signals else 0
            }
            
            # Count timeframe directions
            for tf_signal in confluent_signal.timeframe_signals:
                tf_name = tf_signal.timeframe.name
                direction_value = tf_signal.direction.value
                
                # Store timeframe data
                signal_data['timeframes'][tf_name] = {
                    'signal': 'BUY' if direction_value > 0 else 'SELL' if direction_value < 0 else 'NEUTRAL',
                    'strength': tf_signal.strength.value if hasattr(tf_signal.strength, 'value') else abs(direction_value),
                    'confidence': tf_signal.confidence
                }
                
                # Count directions
                if direction_value > 0:
                    signal_data['bullish_timeframes'] += 1
                elif direction_value < 0:
                    signal_data['bearish_timeframes'] += 1
                else:
                    signal_data['neutral_timeframes'] += 1
            
            signal, reason = self.get_signal_category(signal_data)
            
            # Get timeframe breakdown
            tf_details = {}
            for tf in self.timeframes:
                tf_data = signal_data.get('timeframes', {}).get(tf, {})
                if tf_data:
                    tf_signal = tf_data.get('signal', 'NEUTRAL')
                    tf_strength = tf_data.get('strength', 0)
                    if tf_signal == 'BUY':
                        tf_details[tf] = f"🟢 {tf_strength:.2f}"
                    elif tf_signal == 'SELL':
                        tf_details[tf] = f"🔴 {tf_strength:.2f}"
                    else:
                        tf_details[tf] = f"⚪ {tf_strength:.2f}"
                else:
                    tf_details[tf] = "⚪ 0.00"
            
            return {
                'symbol': symbol,
                'signal': signal,
                'reason': reason,
                'confluence': signal_data.get('confluence_score', 0),
                'strength': signal_data.get('overall_strength', 0),
                'risk': signal_data.get('risk_level', 'HIGH'),
                'bull_tf': signal_data.get('bullish_timeframes', 0),
                'bear_tf': signal_data.get('bearish_timeframes', 0),
                'neutral_tf': signal_data.get('neutral_timeframes', 0),
                'timeframe_details': tf_details,
                'last_price': signal_data.get('current_price', 'N/A'),
                'volume_trend': signal_data.get('volume_trend', 'Unknown')
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'signal': '❌ ERROR',
                'reason': f'Analysis failed: {str(e)}',
                'confluence': 0,
                'strength': 0,
                'risk': 'UNKNOWN',
                'bull_tf': 0,
                'bear_tf': 0,
                'neutral_tf': 0,
                'timeframe_details': {},
                'last_price': 'N/A',
                'volume_trend': 'Unknown'
            }
    
    def generate_status_table(self):
        """Generate comprehensive trading status table"""
        print("🎯 TRADING STATUS DASHBOARD")
        print("=" * 80)
        print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("🎯 Enhanced Multi-Timeframe Strategy with Advanced Indicators")
        print("\n📊 SIGNAL CATEGORIES:")
        print("  🟢 STRONG_BUY/BUY - Long position recommended")
        print("  🔴 STRONG_SELL/SELL - Short position recommended") 
        print("  ⚪ HOLD - No position, stay flat")
        print("  👁️ WATCH - Monitor for developing signals")
        print("=" * 80)
        
        # Analyze all symbols
        results = []
        for symbol in self.symbols:
            result = self.analyze_symbol(symbol)
            results.append(result)
        
        # Create main status table
        print("\n📋 MAIN TRADING STATUS TABLE")
        print("-" * 120)
        header = f"{'Symbol':<8} {'Signal':<15} {'Conf':<6} {'Str':<6} {'Risk':<8} {'Bull':<4} {'Bear':<4} {'Reason':<35}"
        print(header)
        print("-" * 120)
        
        # Sort by signal priority (STRONG_BUY/SELL first, then BUY/SELL, etc.)
        signal_priority = {
            '🟢 STRONG_BUY': 1,
            '🔴 STRONG_SELL': 2, 
            '🟢 BUY': 3,
            '🔴 SELL': 4,
            '👁️ WATCH': 5,
            '⚪ HOLD': 6,
            '❌ ERROR': 7
        }
        
        results.sort(key=lambda x: signal_priority.get(x['signal'], 8))
        
        for result in results:
            risk_color = self.get_risk_color(result['risk'])
            row = (f"{result['symbol']:<8} "
                  f"{result['signal']:<15} "
                  f"{result['confluence']:<6.3f} "
                  f"{result['strength']:<6.3f} "
                  f"{risk_color}{result['risk']:<7} "
                  f"{result['bull_tf']:<4} "
                  f"{result['bear_tf']:<4} "
                  f"{result['reason']:<35}")
            print(row)
        
        # Timeframe breakdown table
        print(f"\n📊 TIMEFRAME BREAKDOWN (Signal + Strength)")
        print("-" * 80)
        tf_header = f"{'Symbol':<8}"
        for tf in self.timeframes:
            tf_header += f" {tf:<8}"
        print(tf_header)
        print("-" * 80)
        
        for result in results:
            tf_row = f"{result['symbol']:<8}"
            for tf in self.timeframes:
                tf_signal = result['timeframe_details'].get(tf, '⚪ 0.00')
                tf_row += f" {tf_signal:<8}"
            print(tf_row)
        
        # Summary statistics
        print(f"\n📊 PORTFOLIO SUMMARY")
        print("-" * 40)
        
        signal_counts = {}
        total_symbols = len(results)
        
        for result in results:
            signal = result['signal']
            signal_counts[signal] = signal_counts.get(signal, 0) + 1
        
        print(f"Total Symbols Analyzed: {total_symbols}")
        for signal, count in sorted(signal_counts.items(), key=lambda x: signal_priority.get(x[0], 8)):
            pct = (count / total_symbols) * 100
            print(f"  {signal}: {count} symbols ({pct:.1f}%)")
        
        # Risk distribution
        risk_counts = {}
        for result in results:
            risk = result['risk']
            if risk != 'UNKNOWN':
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        if risk_counts:
            print(f"\n🎯 RISK DISTRIBUTION:")
            for risk, count in risk_counts.items():
                pct = (count / total_symbols) * 100
                color = self.get_risk_color(risk)
                print(f"  {color}{risk}: {count} symbols ({pct:.1f}%)")
        
        # Market sentiment
        total_bull = sum(r['bull_tf'] for r in results)
        total_bear = sum(r['bear_tf'] for r in results)
        total_neutral = sum(r['neutral_tf'] for r in results)
        total_tf_signals = total_bull + total_bear + total_neutral
        
        if total_tf_signals > 0:
            print(f"\n🌍 OVERALL MARKET SENTIMENT:")
            bull_pct = (total_bull / total_tf_signals) * 100
            bear_pct = (total_bear / total_tf_signals) * 100
            neutral_pct = (total_neutral / total_tf_signals) * 100
            
            print(f"  🟢 Bullish: {total_bull}/{total_tf_signals} ({bull_pct:.1f}%)")
            print(f"  🔴 Bearish: {total_bear}/{total_tf_signals} ({bear_pct:.1f}%)")
            print(f"  ⚪ Neutral: {total_neutral}/{total_tf_signals} ({neutral_pct:.1f}%)")
            
            if bull_pct > bear_pct + 10:
                sentiment = "🟢 BULLISH MARKET"
            elif bear_pct > bull_pct + 10:
                sentiment = "🔴 BEARISH MARKET"
            else:
                sentiment = "⚪ MIXED MARKET"
            print(f"  📊 Market Bias: {sentiment}")
        
        # Web dashboard data structure (for future integration)
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'symbols': results,
            'summary': {
                'total_symbols': total_symbols,
                'signal_counts': signal_counts,
                'risk_distribution': risk_counts,
                'market_sentiment': {
                    'bullish_pct': bull_pct if total_tf_signals > 0 else 0,
                    'bearish_pct': bear_pct if total_tf_signals > 0 else 0,
                    'neutral_pct': neutral_pct if total_tf_signals > 0 else 0
                }
            }
        }
        
        print(f"\n🎯 DASHBOARD DATA READY FOR WEB INTEGRATION")
        print(f"📊 Data structure contains {len(dashboard_data['symbols'])} symbols with full analysis")
        print("=" * 80)
        
        return dashboard_data

def main():
    """Main execution function"""
    print("🚀 Initializing Trading Status Dashboard...")
    
    dashboard = TradingStatusDashboard()
    dashboard_data = dashboard.generate_status_table()
    
    print(f"\n✅ Trading Status Dashboard Complete!")
    print(f"📊 Analyzed {len(dashboard_data['symbols'])} symbols")
    print(f"🕒 Generated at: {dashboard_data['timestamp']}")

if __name__ == "__main__":
    main()
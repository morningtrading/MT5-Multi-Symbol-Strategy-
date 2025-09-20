#!/usr/bin/env python3
"""
Integrated Multi-Symbol Multi-Timeframe Strategy Engine
=======================================================

Advanced trading system that combines:
- Multi-timeframe confluence analysis
- Multi-symbol processing
- Risk management
- Performance tracking
- Unified configuration system

This integrates the new Multi-Timeframe Strategy Engine with our existing
single-timeframe momentum strategy for a comprehensive trading solution.

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: 2.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
import json
import os
import warnings
warnings.filterwarnings('ignore')

# Import our components
from GEN_multi_timeframe_strategy import (
    MultiTimeframeStrategy, ConfluentSignal, TimeFrame, 
    MarketDirection, SignalStrength
)

class IntegratedStrategyEngine:
    """
    Integrated Strategy Engine
    
    Combines multi-timeframe analysis with multi-symbol processing,
    risk management, and performance tracking for a complete trading system.
    """
    
    def __init__(self, config_path: str = "GEN_unified_config.json"):
        """Initialize integrated strategy engine"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.multi_timeframe = MultiTimeframeStrategy(config_path)
        self.symbols = self.config["strategy_settings"]["symbols"]
        self.enabled_symbols = self._get_enabled_symbols()
        
        # Strategy state
        self.signal_cache = {}
        self.performance_metrics = {}
        self.risk_state = {}
        
        # Configuration shortcuts
        self.mtf_config = self.config.get("multi_timeframe_strategy", {})
        self.risk_config = self.config.get("risk_management", {})
        self.strategy_config = self.config.get("strategy_settings", {})
        
        print("🚀 INTEGRATED MULTI-TIMEFRAME STRATEGY ENGINE v2.0")
        print("=" * 70)
        print(f"✅ Multi-timeframe engine: {self.mtf_config.get('enabled', False)}")
        print(f"📊 Active symbols: {len(self.enabled_symbols)}")
        print(f"⚖️  Risk management: Enabled")
        print(f"📈 Performance tracking: Enabled")
    
    def _load_config(self) -> Dict:
        """Load unified configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            raise
    
    def _get_enabled_symbols(self) -> List[str]:
        """Get list of enabled symbols from configuration"""
        enabled = []
        
        for symbol in self.symbols:
            symbol_config = self.config.get("symbol_specific", {}).get(symbol, {})
            if symbol_config.get("enabled", True):  # Default to enabled if not specified
                enabled.append(symbol)
        
        return enabled
    
    def analyze_market_overview(self) -> Dict[str, Dict]:
        """
        Comprehensive market analysis across all symbols and timeframes
        """
        print("\n🔍 COMPREHENSIVE MARKET ANALYSIS")
        print("=" * 70)
        
        results = {}
        
        # Multi-timeframe analysis for all symbols
        mtf_results = self.multi_timeframe.analyze_multiple_symbols(self.enabled_symbols)
        
        # Process and enhance results
        for symbol, confluence_signal in mtf_results.items():
            if confluence_signal is None:
                continue
                
            # Get symbol-specific configuration
            symbol_config = self.config.get("symbol_specific", {}).get(symbol, {})
            
            # Calculate enhanced metrics
            enhanced_analysis = self._enhance_signal_analysis(symbol, confluence_signal, symbol_config)
            
            results[symbol] = {
                "confluence_signal": confluence_signal,
                "enhanced_analysis": enhanced_analysis,
                "symbol_config": symbol_config
            }
            
            # Cache for future use
            self.signal_cache[symbol] = {
                "timestamp": datetime.now(),
                "signal": confluence_signal
            }
        
        # Generate market summary
        market_summary = self._generate_market_summary(results)
        
        print(f"\n📊 MARKET OVERVIEW COMPLETE")
        print(f"✅ Analyzed: {len(results)} symbols")
        print(f"🎯 Strong signals: {market_summary['strong_signals']}")
        print(f"⚠️  High risk: {market_summary['high_risk_count']}")
        
        return {
            "symbol_analyses": results,
            "market_summary": market_summary,
            "timestamp": datetime.now()
        }
    
    def _enhance_signal_analysis(self, symbol: str, confluence_signal: ConfluentSignal, 
                                symbol_config: Dict) -> Dict:
        """Enhance confluence signal with additional analysis"""
        
        # Risk assessment
        risk_assessment = self._assess_symbol_risk(symbol, confluence_signal, symbol_config)
        
        # Position sizing recommendation
        position_sizing = self._calculate_position_sizing(symbol, confluence_signal, symbol_config)
        
        # Entry/exit recommendations
        entry_exit = self._generate_entry_exit_recommendations(symbol, confluence_signal)
        
        # Symbol-specific adjustments
        adjustments = self._apply_symbol_specific_adjustments(symbol, confluence_signal, symbol_config)
        
        return {
            "risk_assessment": risk_assessment,
            "position_sizing": position_sizing,
            "entry_exit": entry_exit,
            "adjustments": adjustments,
            "final_recommendation": self._get_final_recommendation(
                confluence_signal, risk_assessment, adjustments
            )
        }
    
    def _assess_symbol_risk(self, symbol: str, signal: ConfluentSignal, config: Dict) -> Dict:
        """Assess risk for a specific symbol"""
        
        # Base risk from confluence analysis
        base_risk = signal.risk_level
        
        # Symbol-specific risk factors
        asset_class = config.get("risk_parameters", {}).get("asset_class", "unknown")
        
        # Market conditions
        current_time = datetime.now()
        is_trading_hours = self._is_trading_hours(symbol, current_time)
        
        # Volatility assessment from H1 timeframe
        h1_signals = [s for s in signal.timeframe_signals if s.timeframe == TimeFrame.H1]
        volatility_risk = "MEDIUM"
        
        if h1_signals:
            atr_percent = h1_signals[0].indicators.get("atr_percent", 0)
            if atr_percent > 0.01:  # 1%
                volatility_risk = "HIGH"
            elif atr_percent < 0.003:  # 0.3%
                volatility_risk = "LOW"
        
        # Confluence risk adjustment
        if signal.confluence_score >= 0.8:
            confluence_risk = "LOW"
        elif signal.confluence_score >= 0.6:
            confluence_risk = "MEDIUM"
        else:
            confluence_risk = "HIGH"
        
        # Overall risk calculation
        risk_factors = {
            "base_risk": base_risk,
            "asset_class_risk": self._get_asset_class_risk(asset_class),
            "volatility_risk": volatility_risk,
            "confluence_risk": confluence_risk,
            "trading_hours_risk": "LOW" if is_trading_hours else "MEDIUM"
        }
        
        # Calculate overall risk
        overall_risk = self._calculate_overall_risk(risk_factors)
        
        return {
            "overall_risk": overall_risk,
            "risk_factors": risk_factors,
            "risk_score": self._risk_to_score(overall_risk),
            "recommendations": self._get_risk_recommendations(overall_risk)
        }
    
    def _calculate_position_sizing(self, symbol: str, signal: ConfluentSignal, config: Dict) -> Dict:
        """Calculate recommended position sizing"""
        
        # Base position size from confluence
        base_multiplier = signal.position_size_multiplier
        
        # Risk adjustments
        risk_config = config.get("risk_parameters", {})
        coefficient = risk_config.get("coefficient", 1)
        min_lot = risk_config.get("min_lot", 0.01)
        
        # Account risk limits
        max_position_percent = self.risk_config.get("exposure_limits", {}).get("max_position_percent_account", 15.0)
        
        # Calculate position size
        risk_adjusted_multiplier = base_multiplier * (coefficient / 5.0)  # Normalize coefficient
        
        # Apply confidence boost
        if signal.confluence_score >= 0.8 and signal.overall_strength >= 0.7:
            confidence_boost = 1.2
        else:
            confidence_boost = 0.8
        
        final_multiplier = risk_adjusted_multiplier * confidence_boost
        
        # Position size recommendations
        conservative_size = final_multiplier * 0.5
        moderate_size = final_multiplier * 1.0
        aggressive_size = final_multiplier * 1.5
        
        return {
            "base_multiplier": base_multiplier,
            "risk_adjusted": risk_adjusted_multiplier,
            "final_multiplier": final_multiplier,
            "recommendations": {
                "conservative": max(conservative_size, min_lot),
                "moderate": max(moderate_size, min_lot),
                "aggressive": max(aggressive_size, min_lot)
            },
            "max_position_value_percent": max_position_percent
        }
    
    def _generate_entry_exit_recommendations(self, symbol: str, signal: ConfluentSignal) -> Dict:
        """Generate entry and exit recommendations"""
        
        # Current price (from latest H1 signal)
        h1_signals = [s for s in signal.timeframe_signals if s.timeframe == TimeFrame.H1]
        current_price = h1_signals[0].price if h1_signals else 0
        
        # ATR for volatility-based levels
        atr_percent = h1_signals[0].indicators.get("atr_percent", 0.01) if h1_signals else 0.01
        
        recommendations = {}
        
        if signal.recommended_action in ["BUY", "STRONG_BUY"]:
            # Entry recommendations for long positions
            recommendations.update({
                "action": "LONG",
                "entry_strategy": "limit_order" if signal.overall_strength >= 0.7 else "market_order",
                "entry_price_target": current_price * (1 - atr_percent * 0.5),  # Slight pullback
                "stop_loss": current_price * (1 - atr_percent * 2.0),  # 2 ATR below
                "take_profit_1": current_price * (1 + atr_percent * 1.5),  # 1.5 ATR above
                "take_profit_2": current_price * (1 + atr_percent * 3.0),  # 3 ATR above
                "risk_reward_ratio": 1.5,
                "max_hold_hours": 24 if signal.overall_strength >= 0.7 else 12
            })
            
        elif signal.recommended_action in ["SELL", "STRONG_SELL"]:
            # Entry recommendations for short positions
            recommendations.update({
                "action": "SHORT",
                "entry_strategy": "limit_order" if signal.overall_strength >= 0.7 else "market_order",
                "entry_price_target": current_price * (1 + atr_percent * 0.5),  # Slight bounce
                "stop_loss": current_price * (1 + atr_percent * 2.0),  # 2 ATR above
                "take_profit_1": current_price * (1 - atr_percent * 1.5),  # 1.5 ATR below
                "take_profit_2": current_price * (1 - atr_percent * 3.0),  # 3 ATR below
                "risk_reward_ratio": 1.5,
                "max_hold_hours": 24 if signal.overall_strength >= 0.7 else 12
            })
            
        else:
            # Hold recommendations
            recommendations.update({
                "action": "HOLD",
                "reason": "Insufficient confluence or mixed signals",
                "wait_for": "Higher confluence score or clearer directional signals",
                "recheck_in_minutes": 30
            })
        
        return recommendations
    
    def _apply_symbol_specific_adjustments(self, symbol: str, signal: ConfluentSignal, 
                                         config: Dict) -> Dict:
        """Apply symbol-specific adjustments to the analysis"""
        
        adjustments = {"applied": [], "multipliers": {}}
        
        # Confidence override
        min_confidence_override = config.get("min_confidence_override")
        if min_confidence_override and signal.confluence_score < min_confidence_override:
            adjustments["applied"].append("confidence_filter_failed")
            adjustments["multipliers"]["confidence"] = 0.5
        
        # Correlation checks for crypto symbols
        correlated_symbols = config.get("correlation_with", [])
        if correlated_symbols:
            # This would require analyzing correlated symbols - placeholder for now
            adjustments["applied"].append("correlation_check_needed")
        
        # Trading hours filter
        if config.get("trading_hours_only", False):
            if not self._is_trading_hours(symbol, datetime.now()):
                adjustments["applied"].append("outside_trading_hours")
                adjustments["multipliers"]["timing"] = 0.3
        
        # News/economic calendar filter
        if config.get("economic_calendar_filter", False):
            # Placeholder for news filter
            adjustments["applied"].append("news_filter_check")
        
        # High volatility filter
        high_vol_filter = config.get("special_conditions", {}).get("high_volatility_filter", False)
        if high_vol_filter:
            h1_signals = [s for s in signal.timeframe_signals if s.timeframe == TimeFrame.H1]
            if h1_signals:
                atr_percent = h1_signals[0].indicators.get("atr_percent", 0)
                if atr_percent > 0.02:  # 2% volatility threshold
                    adjustments["applied"].append("high_volatility_reduction")
                    adjustments["multipliers"]["volatility"] = 0.7
        
        return adjustments
    
    def _get_final_recommendation(self, signal: ConfluentSignal, risk_assessment: Dict, 
                                adjustments: Dict) -> Dict:
        """Generate final trading recommendation"""
        
        # Start with base recommendation
        base_action = signal.recommended_action
        base_strength = signal.overall_strength
        base_confidence = signal.confluence_score
        
        # Apply adjustment multipliers
        final_strength = base_strength
        for multiplier in adjustments.get("multipliers", {}).values():
            final_strength *= multiplier
        
        # Risk-adjusted recommendation
        risk_score = risk_assessment["risk_score"]
        
        if risk_score > 0.7:  # High risk
            if base_action in ["STRONG_BUY", "STRONG_SELL"]:
                final_action = "HOLD"
                reason = "Risk too high for strong action"
            elif base_action in ["BUY", "SELL"]:
                final_action = "WATCH"
                reason = "Reduce to watch due to high risk"
            else:
                final_action = "HOLD"
                reason = "High risk environment"
        else:
            final_action = base_action
            reason = "Risk acceptable for recommended action"
        
        # Confidence check
        if base_confidence < 0.5:
            final_action = "HOLD"
            reason = "Insufficient confluence across timeframes"
        
        return {
            "final_action": final_action,
            "original_action": base_action,
            "adjusted_strength": final_strength,
            "risk_adjusted": final_strength != base_strength,
            "reason": reason,
            "confidence_level": self._get_confidence_level(base_confidence, final_strength),
            "trade_priority": self._calculate_trade_priority(final_action, final_strength, base_confidence)
        }
    
    def _generate_market_summary(self, results: Dict) -> Dict:
        """Generate overall market summary"""
        
        total_symbols = len(results)
        strong_signals = 0
        buy_signals = 0
        sell_signals = 0
        hold_signals = 0
        high_risk_count = 0
        
        for symbol, analysis in results.items():
            signal = analysis["confluence_signal"]
            risk = analysis["enhanced_analysis"]["risk_assessment"]["overall_risk"]
            
            action = signal.recommended_action
            if action in ["STRONG_BUY", "STRONG_SELL"]:
                strong_signals += 1
            
            if "BUY" in action:
                buy_signals += 1
            elif "SELL" in action:
                sell_signals += 1
            else:
                hold_signals += 1
            
            if risk == "HIGH":
                high_risk_count += 1
        
        market_bias = "NEUTRAL"
        if buy_signals > sell_signals * 1.5:
            market_bias = "BULLISH"
        elif sell_signals > buy_signals * 1.5:
            market_bias = "BEARISH"
        
        return {
            "total_symbols": total_symbols,
            "strong_signals": strong_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "high_risk_count": high_risk_count,
            "market_bias": market_bias,
            "market_strength": strong_signals / max(total_symbols, 1),
            "risk_level": "HIGH" if high_risk_count > total_symbols * 0.5 else "MEDIUM"
        }
    
    # Utility methods
    def _get_asset_class_risk(self, asset_class: str) -> str:
        """Get risk level based on asset class"""
        risk_map = {
            "crypto": "HIGH",
            "forex": "MEDIUM",
            "index": "LOW",
            "commodity": "MEDIUM",
            "stock": "MEDIUM"
        }
        return risk_map.get(asset_class, "MEDIUM")
    
    def _calculate_overall_risk(self, risk_factors: Dict) -> str:
        """Calculate overall risk from individual factors"""
        risk_scores = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3
        }
        
        total_score = sum(risk_scores.get(risk, 2) for risk in risk_factors.values())
        avg_score = total_score / len(risk_factors)
        
        if avg_score >= 2.5:
            return "HIGH"
        elif avg_score >= 1.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _risk_to_score(self, risk_level: str) -> float:
        """Convert risk level to numeric score"""
        return {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.8}.get(risk_level, 0.5)
    
    def _get_risk_recommendations(self, risk_level: str) -> List[str]:
        """Get risk management recommendations"""
        recommendations = {
            "LOW": ["Consider standard position sizing", "Monitor for changes"],
            "MEDIUM": ["Reduce position size by 25%", "Set tighter stop losses", "Monitor closely"],
            "HIGH": ["Reduce position size by 50%", "Consider avoiding trade", "Wait for better setup"]
        }
        return recommendations.get(risk_level, [])
    
    def _is_trading_hours(self, symbol: str, timestamp: datetime) -> bool:
        """Check if current time is within trading hours for symbol"""
        # Simplified - crypto trades 24/7, others have specific hours
        symbol_config = self.config.get("symbol_specific", {}).get(symbol, {})
        if symbol_config.get("asset_class") == "crypto":
            return True
        
        # For other assets, check trading hours (simplified)
        hour = timestamp.hour
        weekday = timestamp.weekday()
        
        # Basic market hours: weekdays 9 AM - 4 PM
        if weekday < 5 and 9 <= hour < 16:
            return True
        return False
    
    def _get_confidence_level(self, confluence: float, strength: float) -> str:
        """Get confidence level description"""
        combined = (confluence + strength) / 2
        
        if combined >= 0.8:
            return "Very High"
        elif combined >= 0.6:
            return "High"
        elif combined >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def _calculate_trade_priority(self, action: str, strength: float, confidence: float) -> int:
        """Calculate trade priority (1-10, higher = more urgent)"""
        if action == "HOLD":
            return 1
        
        base_priority = 5
        
        # Adjust for action type
        if action in ["STRONG_BUY", "STRONG_SELL"]:
            base_priority += 3
        elif action in ["BUY", "SELL"]:
            base_priority += 1
        
        # Adjust for strength and confidence
        base_priority += int((strength + confidence) * 2)
        
        return min(base_priority, 10)
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive analysis report"""
        
        # Run full market analysis
        analysis_results = self.analyze_market_overview()
        
        report = []
        report.append("🚀 INTEGRATED MULTI-TIMEFRAME STRATEGY REPORT")
        report.append("=" * 80)
        report.append(f"📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Market summary
        summary = analysis_results["market_summary"]
        report.append("\n📊 MARKET OVERVIEW")
        report.append("-" * 50)
        report.append(f"Market Bias: {summary['market_bias']}")
        report.append(f"Market Strength: {summary['market_strength']:.2f}")
        report.append(f"Overall Risk: {summary['risk_level']}")
        report.append(f"Strong Signals: {summary['strong_signals']}/{summary['total_symbols']}")
        report.append(f"Buy vs Sell: {summary['buy_signals']} vs {summary['sell_signals']}")
        
        # Individual symbol analysis
        report.append("\n📈 SYMBOL ANALYSIS")
        report.append("-" * 50)
        
        for symbol, analysis in analysis_results["symbol_analyses"].items():
            signal = analysis["confluence_signal"]
            enhanced = analysis["enhanced_analysis"]
            final_rec = enhanced["final_recommendation"]
            
            report.append(f"\n🔍 {symbol}:")
            report.append(f"   Action: {final_rec['final_action']} (Priority: {final_rec['trade_priority']})")
            report.append(f"   Confluence: {signal.confluence_score:.2f} | Strength: {signal.overall_strength:.2f}")
            report.append(f"   Risk: {enhanced['risk_assessment']['overall_risk']}")
            report.append(f"   Confidence: {final_rec['confidence_level']}")
            
            if final_rec['final_action'] != "HOLD":
                entry_exit = enhanced["entry_exit"]
                if "action" in entry_exit:
                    report.append(f"   Direction: {entry_exit['action']}")
                    report.append(f"   Entry: {entry_exit.get('entry_price_target', 'Market')}")
                    report.append(f"   Risk/Reward: {entry_exit.get('risk_reward_ratio', 'N/A')}")
        
        return "\n".join(report)

def main():
    """Main execution for testing"""
    print("🚀 INTEGRATED MULTI-TIMEFRAME STRATEGY ENGINE")
    print("=" * 80)
    
    try:
        # Initialize integrated engine
        engine = IntegratedStrategyEngine()
        
        # Generate comprehensive report
        report = engine.generate_comprehensive_report()
        print(report)
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS COMPLETE - System ready for live trading integration")
        
    except Exception as e:
        print(f"❌ Error in integrated analysis: {e}")
        raise

if __name__ == "__main__":
    main()
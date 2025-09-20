#!/usr/bin/env python3
"""
Enhanced Multi-Timeframe Strategy with Advanced Technical Indicators
===================================================================

Advanced strategy engine that combines the multi-timeframe analysis framework
with comprehensive technical indicators including Stochastic, Williams %R, 
Ichimoku Cloud, ADX, CCI, Parabolic SAR, and volume-based indicators.

This enhanced version provides:
- All basic indicators (RSI, MACD, Bollinger Bands, ATR)
- Advanced momentum oscillators (Stochastic, Williams %R, CCI)
- Trend analysis indicators (ADX, Ichimoku, PSAR)
- Volatility channels (Keltner, Donchian)
- Volume analysis (MFI, OBV, A/D Line, CMF)
- Composite indicators (Fisher Transform)

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
    MarketDirection, SignalStrength, TimeframeSignal
)
from GEN_advanced_technical_indicators import AdvancedTechnicalIndicators

class EnhancedMultiTimeframeStrategy(MultiTimeframeStrategy):
    """
    Enhanced Multi-Timeframe Strategy
    
    Extends the base multi-timeframe strategy with advanced technical indicators
    for more sophisticated market analysis and signal generation.
    """
    
    def __init__(self, config_path: str = "GEN_unified_config.json"):
        """Initialize enhanced multi-timeframe strategy"""
        super().__init__(config_path)
        
        # Initialize advanced indicators library
        self.advanced_indicators = AdvancedTechnicalIndicators()
        
        # Enhanced indicator configuration
        self.enhanced_config = self.config.get("enhanced_indicators", self._get_enhanced_default_config())
        
        print("🚀 Enhanced Multi-Timeframe Strategy with Advanced Indicators initialized")
    
    def _get_enhanced_default_config(self) -> Dict:
        """Get enhanced default configuration for advanced indicators"""
        return {
            "enabled": True,
            "momentum_weight": 0.25,
            "trend_weight": 0.35,
            "volatility_weight": 0.20,
            "volume_weight": 0.20,
            "indicators": {
                "stochastic": {"k_period": 14, "d_period": 3, "smooth_k": 3, "weight": 0.15},
                "williams_r": {"period": 14, "weight": 0.10},
                "cci": {"period": 20, "weight": 0.15},
                "roc": {"period": 12, "weight": 0.10},
                "adx": {"period": 14, "weight": 0.20},
                "ichimoku": {"tenkan_period": 9, "kijun_period": 26, "senkou_b_period": 52, "chikou_period": 26, "weight": 0.25},
                "psar": {"af_start": 0.02, "af_increment": 0.02, "af_maximum": 0.2, "weight": 0.15},
                "keltner": {"period": 20, "multiplier": 2.0, "ma_type": "ema", "weight": 0.10},
                "donchian": {"period": 20, "weight": 0.10},
                "mfi": {"period": 14, "weight": 0.15},
                "cmf": {"period": 20, "weight": 0.10},
                "fisher": {"period": 9, "weight": 0.15}
            }
        }
    
    def calculate_enhanced_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate enhanced technical indicators including basic + advanced
        
        Args:
            data: DataFrame with OHLC data
            
        Returns:
            DataFrame with all technical indicators
        """
        # Start with basic indicators from parent class
        df = self.calculate_technical_indicators(data)
        
        # Add advanced indicators
        if self.enhanced_config.get("enabled", True):
            # Filter out weight parameters from indicator configs
            filtered_config = {}
            for indicator, params in self.enhanced_config.get("indicators", {}).items():
                filtered_config[indicator] = {k: v for k, v in params.items() if k != 'weight'}
            
            df = self.advanced_indicators.calculate_all_indicators(df, filtered_config)
        
        return df
    
    def generate_enhanced_timeframe_signal(self, symbol: str, timeframe: TimeFrame, 
                                         current_time: datetime = None) -> TimeframeSignal:
        """
        Generate enhanced trading signal for a specific timeframe using advanced indicators
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            current_time: Specific time for analysis (None for latest)
            
        Returns:
            Enhanced TimeframeSignal with advanced indicator analysis
        """
        if symbol not in self.data_cache:
            raise ValueError(f"Data not loaded for symbol: {symbol}")
        
        if timeframe not in self.data_cache[symbol]:
            raise ValueError(f"Timeframe {timeframe.name} not available for {symbol}")
        
        # Get data for this timeframe
        data = self.data_cache[symbol][timeframe]
        
        # Calculate enhanced indicators
        df = self.calculate_enhanced_technical_indicators(data)
        
        # Get latest values (or at specific time if provided)
        if current_time:
            idx = df.index.get_indexer([current_time], method='nearest')[0]
            latest = df.iloc[idx]
            signal_time = df.index[idx]
        else:
            latest = df.iloc[-1]
            signal_time = df.index[-1]
        
        # Enhanced signal generation with weighted scoring
        signals = []
        indicators = {}
        signal_weights = []
        
        # ========================================
        # BASIC INDICATORS (from parent class)
        # ========================================
        
        # RSI signals
        rsi_signal = 0
        if latest['rsi'] < 30:
            rsi_signal = 1  # Oversold
        elif latest['rsi'] > 70:
            rsi_signal = -1  # Overbought
        
        signals.append(rsi_signal)
        signal_weights.append(0.15)
        indicators['rsi_value'] = latest['rsi']
        indicators['rsi_signal'] = rsi_signal
        
        # MACD signals
        macd_signal = 0
        if latest['macd'] > latest['macd_signal'] and latest['macd_histogram'] > 0:
            macd_signal = 1  # Bullish
        elif latest['macd'] < latest['macd_signal'] and latest['macd_histogram'] < 0:
            macd_signal = -1  # Bearish
        
        signals.append(macd_signal)
        signal_weights.append(0.15)
        indicators['macd_value'] = latest['macd']
        indicators['macd_signal'] = macd_signal
        
        # Bollinger Band signals
        bb_signal = 0
        if latest['bb_position'] < 0.2:
            bb_signal = 1  # Near lower band
        elif latest['bb_position'] > 0.8:
            bb_signal = -1  # Near upper band
        
        signals.append(bb_signal)
        signal_weights.append(0.10)
        indicators['bb_position'] = latest['bb_position']
        indicators['bb_signal'] = bb_signal
        
        # ========================================
        # MOMENTUM OSCILLATORS
        # ========================================
        
        if self.enhanced_config.get("enabled", True):
            
            # Stochastic Oscillator
            if 'stoch_k' in df.columns:
                stoch_signal = latest.get('stoch_signal', 0)
                stoch_crossover = latest.get('stoch_crossover', 0)
                
                # Combine level and crossover signals
                combined_stoch = 0
                if stoch_signal != 0:
                    combined_stoch = stoch_signal
                elif stoch_crossover != 0:
                    combined_stoch = stoch_crossover * 0.5  # Crossover less strong than level
                
                signals.append(combined_stoch)
                signal_weights.append(self.enhanced_config["indicators"]["stochastic"]["weight"])
                indicators['stoch_k'] = latest['stoch_k']
                indicators['stoch_d'] = latest['stoch_d']
                indicators['stoch_signal'] = combined_stoch
            
            # Williams %R
            if 'williams_r' in df.columns:
                williams_signal = latest.get('williams_r_signal', 0)
                signals.append(williams_signal)
                signal_weights.append(self.enhanced_config["indicators"]["williams_r"]["weight"])
                indicators['williams_r'] = latest['williams_r']
                indicators['williams_r_signal'] = williams_signal
            
            # CCI
            if 'cci' in df.columns:
                cci_signal = latest.get('cci_signal', 0)
                signals.append(cci_signal)
                signal_weights.append(self.enhanced_config["indicators"]["cci"]["weight"])
                indicators['cci'] = latest['cci']
                indicators['cci_signal'] = cci_signal
            
            # Rate of Change
            if 'roc' in df.columns:
                roc_signal = latest.get('roc_signal', 0)
                # Apply threshold to ROC for stronger signals
                roc_value = latest['roc']
                enhanced_roc_signal = 0
                if roc_value > 2.0:  # Strong positive momentum
                    enhanced_roc_signal = 1
                elif roc_value < -2.0:  # Strong negative momentum
                    enhanced_roc_signal = -1
                
                signals.append(enhanced_roc_signal)
                signal_weights.append(self.enhanced_config["indicators"]["roc"]["weight"])
                indicators['roc'] = roc_value
                indicators['roc_signal'] = enhanced_roc_signal
            
            # ========================================
            # TREND INDICATORS
            # ========================================
            
            # ADX - Trend Strength
            if 'adx' in df.columns:
                adx_signal = latest.get('adx_signal', 0)
                # Enhance ADX signal with trend strength
                adx_value = latest['adx']
                di_plus = latest['di_plus']
                di_minus = latest['di_minus']
                
                enhanced_adx_signal = 0
                if adx_value > 25:  # Strong trend
                    if di_plus > di_minus:
                        enhanced_adx_signal = 1  # Strong uptrend
                    else:
                        enhanced_adx_signal = -1  # Strong downtrend
                elif adx_value > 20:  # Moderate trend
                    if di_plus > di_minus:
                        enhanced_adx_signal = 0.5  # Moderate uptrend
                    else:
                        enhanced_adx_signal = -0.5  # Moderate downtrend
                
                signals.append(enhanced_adx_signal)
                signal_weights.append(self.enhanced_config["indicators"]["adx"]["weight"])
                indicators['adx'] = adx_value
                indicators['di_plus'] = di_plus
                indicators['di_minus'] = di_minus
                indicators['adx_signal'] = enhanced_adx_signal
            
            # Ichimoku Cloud
            if 'ichimoku_tenkan' in df.columns:
                ichimoku_signal = latest.get('ichimoku_signal', 0)
                
                # Enhanced Ichimoku analysis
                price = latest['close']
                cloud_top = latest.get('ichimoku_cloud_top', price)
                cloud_bottom = latest.get('ichimoku_cloud_bottom', price)
                tenkan = latest['ichimoku_tenkan']
                kijun = latest['ichimoku_kijun']
                
                enhanced_ichimoku_signal = 0
                
                # Strong bullish: price above cloud, tenkan > kijun
                if price > cloud_top and tenkan > kijun:
                    enhanced_ichimoku_signal = 1
                # Moderate bullish: price above cloud but tenkan <= kijun
                elif price > cloud_top:
                    enhanced_ichimoku_signal = 0.5
                # Strong bearish: price below cloud, tenkan < kijun
                elif price < cloud_bottom and tenkan < kijun:
                    enhanced_ichimoku_signal = -1
                # Moderate bearish: price below cloud but tenkan >= kijun
                elif price < cloud_bottom:
                    enhanced_ichimoku_signal = -0.5
                # Inside cloud - neutral with slight bias
                else:
                    if tenkan > kijun:
                        enhanced_ichimoku_signal = 0.2
                    else:
                        enhanced_ichimoku_signal = -0.2
                
                signals.append(enhanced_ichimoku_signal)
                signal_weights.append(self.enhanced_config["indicators"]["ichimoku"]["weight"])
                indicators['ichimoku_tenkan'] = tenkan
                indicators['ichimoku_kijun'] = kijun
                indicators['ichimoku_signal'] = enhanced_ichimoku_signal
            
            # Parabolic SAR
            if 'psar' in df.columns:
                psar_signal = latest.get('psar_signal', 0)
                psar_value = latest['psar']
                price = latest['close']
                
                # Current position relative to PSAR
                current_psar_signal = 0
                if price > psar_value:
                    current_psar_signal = 0.5  # Above PSAR - bullish bias
                else:
                    current_psar_signal = -0.5  # Below PSAR - bearish bias
                
                # Combine reversal signal with current position
                combined_psar_signal = psar_signal if psar_signal != 0 else current_psar_signal
                
                signals.append(combined_psar_signal)
                signal_weights.append(self.enhanced_config["indicators"]["psar"]["weight"])
                indicators['psar'] = psar_value
                indicators['psar_signal'] = combined_psar_signal
            
            # ========================================
            # VOLATILITY INDICATORS
            # ========================================
            
            # Keltner Channels
            if 'keltner_upper' in df.columns:
                keltner_signal = latest.get('keltner_signal', 0)
                keltner_position = latest.get('keltner_position', 0.5)
                
                # Enhanced Keltner analysis
                enhanced_keltner_signal = 0
                if keltner_position < 0.1:
                    enhanced_keltner_signal = 1  # Very oversold
                elif keltner_position < 0.3:
                    enhanced_keltner_signal = 0.5  # Oversold
                elif keltner_position > 0.9:
                    enhanced_keltner_signal = -1  # Very overbought
                elif keltner_position > 0.7:
                    enhanced_keltner_signal = -0.5  # Overbought
                
                signals.append(enhanced_keltner_signal)
                signal_weights.append(self.enhanced_config["indicators"]["keltner"]["weight"])
                indicators['keltner_position'] = keltner_position
                indicators['keltner_signal'] = enhanced_keltner_signal
            
            # Donchian Channels
            if 'donchian_upper' in df.columns:
                donchian_signal = latest.get('donchian_signal', 0)
                donchian_position = latest.get('donchian_position', 0.5)
                
                # Donchian breakout signals are more reliable at extremes
                enhanced_donchian_signal = 0
                if donchian_signal == 1 and donchian_position >= 0.95:
                    enhanced_donchian_signal = 1  # Strong breakout above
                elif donchian_signal == -1 and donchian_position <= 0.05:
                    enhanced_donchian_signal = -1  # Strong breakdown below
                
                signals.append(enhanced_donchian_signal)
                signal_weights.append(self.enhanced_config["indicators"]["donchian"]["weight"])
                indicators['donchian_position'] = donchian_position
                indicators['donchian_signal'] = enhanced_donchian_signal
            
            # ========================================
            # VOLUME INDICATORS
            # ========================================
            
            # Money Flow Index
            if 'mfi' in df.columns:
                mfi_signal = latest.get('mfi_signal', 0)
                mfi_value = latest['mfi']
                
                # Enhanced MFI with gradual zones
                enhanced_mfi_signal = 0
                if mfi_value < 15:
                    enhanced_mfi_signal = 1  # Very oversold
                elif mfi_value < 25:
                    enhanced_mfi_signal = 0.5  # Oversold
                elif mfi_value > 85:
                    enhanced_mfi_signal = -1  # Very overbought
                elif mfi_value > 75:
                    enhanced_mfi_signal = -0.5  # Overbought
                
                signals.append(enhanced_mfi_signal)
                signal_weights.append(self.enhanced_config["indicators"]["mfi"]["weight"])
                indicators['mfi'] = mfi_value
                indicators['mfi_signal'] = enhanced_mfi_signal
            
            # Chaikin Money Flow
            if 'cmf' in df.columns:
                cmf_signal = latest.get('cmf_signal', 0)
                cmf_value = latest['cmf']
                
                # Enhanced CMF with stronger thresholds
                enhanced_cmf_signal = 0
                if cmf_value > 0.15:
                    enhanced_cmf_signal = 1  # Strong buying pressure
                elif cmf_value > 0.05:
                    enhanced_cmf_signal = 0.5  # Moderate buying pressure
                elif cmf_value < -0.15:
                    enhanced_cmf_signal = -1  # Strong selling pressure
                elif cmf_value < -0.05:
                    enhanced_cmf_signal = -0.5  # Moderate selling pressure
                
                signals.append(enhanced_cmf_signal)
                signal_weights.append(self.enhanced_config["indicators"]["cmf"]["weight"])
                indicators['cmf'] = cmf_value
                indicators['cmf_signal'] = enhanced_cmf_signal
            
            # ========================================
            # COMPOSITE INDICATORS
            # ========================================
            
            # Fisher Transform
            if 'fisher_transform' in df.columns:
                fisher_signal = latest.get('fisher_signal', 0)
                fisher_value = latest['fisher_transform']
                
                # Enhanced Fisher Transform analysis
                enhanced_fisher_signal = 0
                if fisher_value > 2:
                    enhanced_fisher_signal = -1  # Very overbought
                elif fisher_value > 1:
                    enhanced_fisher_signal = -0.5  # Overbought
                elif fisher_value < -2:
                    enhanced_fisher_signal = 1  # Very oversold
                elif fisher_value < -1:
                    enhanced_fisher_signal = 0.5  # Oversold
                
                # Combine with crossover signal
                if fisher_signal != 0:
                    enhanced_fisher_signal = (enhanced_fisher_signal + fisher_signal) / 2
                
                signals.append(enhanced_fisher_signal)
                signal_weights.append(self.enhanced_config["indicators"]["fisher"]["weight"])
                indicators['fisher_transform'] = fisher_value
                indicators['fisher_signal'] = enhanced_fisher_signal
        
        # ========================================
        # WEIGHTED SIGNAL AGGREGATION
        # ========================================
        
        # Calculate weighted signal sum
        weighted_signal_sum = sum(signal * weight for signal, weight in zip(signals, signal_weights))
        total_weight = sum(signal_weights)
        
        if total_weight > 0:
            normalized_signal = weighted_signal_sum / total_weight
        else:
            normalized_signal = 0
        
        # Determine direction and strength based on enhanced analysis
        if normalized_signal >= 0.6:
            direction = MarketDirection.STRONG_BUY
            strength = SignalStrength.VERY_STRONG
        elif normalized_signal >= 0.3:
            direction = MarketDirection.BUY
            strength = SignalStrength.STRONG
        elif normalized_signal >= 0.1:
            direction = MarketDirection.BUY
            strength = SignalStrength.WEAK
        elif normalized_signal <= -0.6:
            direction = MarketDirection.STRONG_SELL
            strength = SignalStrength.VERY_STRONG
        elif normalized_signal <= -0.3:
            direction = MarketDirection.SELL
            strength = SignalStrength.STRONG
        elif normalized_signal <= -0.1:
            direction = MarketDirection.SELL
            strength = SignalStrength.WEAK
        else:
            direction = MarketDirection.NEUTRAL
            strength = SignalStrength.NEUTRAL
        
        # Calculate confidence based on signal agreement and strength
        non_zero_signals = [abs(s) for s in signals if s != 0]
        if non_zero_signals:
            confidence = min(abs(normalized_signal) * 2, 1.0)  # Scale to 0-1
        else:
            confidence = 0.0
        
        # Add momentum and volatility context
        indicators['momentum_20'] = latest.get('momentum_20', 0)
        indicators['atr_percent'] = latest.get('atr_percent', 0)
        indicators['normalized_signal'] = normalized_signal
        indicators['signal_count'] = len([s for s in signals if s != 0])
        
        return TimeframeSignal(
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            confidence=confidence,
            indicators=indicators,
            timestamp=signal_time,
            price=latest['close']
        )
    
    def analyze_symbol_enhanced(self, symbol: str, current_time: datetime = None) -> ConfluentSignal:
        """
        Enhanced symbol analysis using advanced indicators
        
        Args:
            symbol: Trading symbol
            current_time: Specific time for analysis
            
        Returns:
            Enhanced ConfluentSignal with advanced indicator analysis
        """
        if symbol not in self.data_cache:
            if not self.load_data(symbol):
                raise ValueError(f"Failed to load data for {symbol}")
        
        # Generate enhanced signals for all timeframes
        timeframe_signals = []
        for tf in self.timeframes:
            if tf in self.data_cache[symbol]:
                try:
                    signal = self.generate_enhanced_timeframe_signal(symbol, tf, current_time)
                    timeframe_signals.append(signal)
                except Exception as e:
                    print(f"⚠️  Error generating enhanced signal for {tf.name}: {e}")
        
        if not timeframe_signals:
            raise ValueError(f"No valid enhanced signals generated for {symbol}")
        
        # Calculate enhanced weighted consensus
        weighted_direction = 0
        total_weight = 0
        agreeing_timeframes = 0
        
        for signal in timeframe_signals:
            weight = self.timeframe_weights.get(signal.timeframe, 0.1)
            direction_value = signal.direction.value
            confidence = signal.confidence
            
            # Enhanced weighting with indicator count and signal strength
            indicator_count_bonus = min(signal.indicators.get('signal_count', 0) / 10, 0.2)  # Bonus for more indicators
            adjusted_weight = weight * (confidence + indicator_count_bonus)
            
            weighted_direction += direction_value * adjusted_weight
            total_weight += adjusted_weight
            
            # Count agreeing timeframes
            if abs(direction_value) > 0:
                agreeing_timeframes += 1
        
        # Normalize weighted direction
        if total_weight > 0:
            normalized_direction = weighted_direction / total_weight
        else:
            normalized_direction = 0
        
        # Enhanced direction classification
        if normalized_direction >= 1.8:
            overall_direction = MarketDirection.STRONG_BUY
        elif normalized_direction >= 0.6:
            overall_direction = MarketDirection.BUY
        elif normalized_direction <= -1.8:
            overall_direction = MarketDirection.STRONG_SELL
        elif normalized_direction <= -0.6:
            overall_direction = MarketDirection.SELL
        else:
            overall_direction = MarketDirection.NEUTRAL
        
        # Enhanced confluence scoring with indicator diversity bonus
        base_confluence = agreeing_timeframes / len(timeframe_signals)
        
        # Bonus for diverse indicator signals across timeframes
        total_indicators = sum(signal.indicators.get('signal_count', 0) for signal in timeframe_signals)
        indicator_diversity_bonus = min(total_indicators / (len(timeframe_signals) * 15), 0.1)
        
        confluence_score = min(base_confluence + indicator_diversity_bonus, 1.0)
        
        # Enhanced overall strength
        overall_strength = min(abs(normalized_direction), 1.0)
        
        # Enhanced action determination
        enhanced_confluence_threshold = 0.65  # Slightly higher threshold for enhanced system
        
        if confluence_score >= enhanced_confluence_threshold and overall_strength >= 0.6:
            if overall_direction.value > 0:
                recommended_action = "STRONG_BUY" if overall_strength >= 0.8 else "BUY"
            else:
                recommended_action = "STRONG_SELL" if overall_strength >= 0.8 else "SELL"
            
            risk_level = "LOW" if confluence_score >= 0.8 else "MEDIUM"
            position_size_multiplier = confluence_score * overall_strength * 1.1  # Bonus for enhanced system
        else:
            recommended_action = "HOLD"
            risk_level = "HIGH"
            position_size_multiplier = 0.5
        
        # Use the most recent timestamp
        latest_timestamp = max(signal.timestamp for signal in timeframe_signals)
        
        return ConfluentSignal(
            symbol=symbol,
            overall_direction=overall_direction,
            overall_strength=overall_strength,
            confluence_score=confluence_score,
            timeframe_signals=timeframe_signals,
            recommended_action=recommended_action,
            risk_level=risk_level,
            position_size_multiplier=position_size_multiplier,
            timestamp=latest_timestamp
        )

def main():
    """Main execution for testing enhanced strategy"""
    print("🚀 ENHANCED MULTI-TIMEFRAME STRATEGY WITH ADVANCED INDICATORS")
    print("=" * 80)
    
    try:
        # Initialize enhanced strategy
        strategy = EnhancedMultiTimeframeStrategy()
        
        # Test symbols with high-quality data
        test_symbols = ["BTCUSD", "ETHUSD"]
        
        print(f"\n🔍 Testing enhanced analysis on {len(test_symbols)} symbols...")
        
        results = {}
        for symbol in test_symbols:
            print(f"\n📊 Enhanced analysis for {symbol}:")
            try:
                signal = strategy.analyze_symbol_enhanced(symbol)
                results[symbol] = signal
                
                direction_icon = strategy._get_direction_icon(signal.overall_direction)
                print(f"   {direction_icon} {signal.recommended_action}")
                print(f"   📈 Strength: {signal.overall_strength:.3f} | Confluence: {signal.confluence_score:.3f}")
                print(f"   🎯 Enhanced Analysis: {len(signal.timeframe_signals)} timeframes")
                
                # Show indicator count for each timeframe
                for tf_signal in signal.timeframe_signals:
                    indicator_count = tf_signal.indicators.get('signal_count', 0)
                    print(f"      {tf_signal.timeframe.name}: {indicator_count} active indicators")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[symbol] = None
        
        print(f"\n✅ Enhanced analysis complete!")
        print(f"📊 Results: {len([r for r in results.values() if r])} successful analyses")
        
    except Exception as e:
        print(f"❌ Error in enhanced strategy testing: {e}")
        raise

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Multi-Timeframe Strategy Engine
==============================

Advanced strategy framework supporting multiple timeframes for signal generation,
confluence detection, and hierarchical decision making.

Features:
- Multi-timeframe data handling (M1, M5, M15, H1, H4, D1)
- Signal aggregation across timeframes
- Confluence scoring system
- Timeframe-specific entry/exit rules
- Risk-adjusted position sizing

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from enum import Enum
import json
import os
import warnings
warnings.filterwarnings('ignore')

class TimeFrame(Enum):
    """Supported timeframes"""
    M1 = "1T"      # 1 minute
    M5 = "5T"      # 5 minutes
    M15 = "15T"    # 15 minutes
    H1 = "1H"      # 1 hour
    H4 = "4H"      # 4 hours
    D1 = "1D"      # 1 day

class SignalStrength(Enum):
    """Signal strength levels"""
    VERY_WEAK = 0.2
    WEAK = 0.4
    NEUTRAL = 0.5
    STRONG = 0.6
    VERY_STRONG = 0.8
    EXTREMELY_STRONG = 1.0

class MarketDirection(Enum):
    """Market direction signals"""
    STRONG_SELL = -2
    SELL = -1
    NEUTRAL = 0
    BUY = 1
    STRONG_BUY = 2

@dataclass
class TimeframeSignal:
    """Signal from a specific timeframe"""
    timeframe: TimeFrame
    direction: MarketDirection
    strength: SignalStrength
    confidence: float  # 0-1
    indicators: Dict[str, float]  # Supporting indicator values
    timestamp: datetime
    price: float
    
@dataclass
class ConfluentSignal:
    """Aggregated signal from multiple timeframes"""
    symbol: str
    overall_direction: MarketDirection
    overall_strength: float
    confluence_score: float  # 0-1 (higher = more timeframes agree)
    timeframe_signals: List[TimeframeSignal]
    recommended_action: str
    risk_level: str
    position_size_multiplier: float
    timestamp: datetime

class MultiTimeframeStrategy:
    """
    Multi-Timeframe Strategy Engine
    
    Processes multiple timeframes to generate confluent trading signals
    with hierarchical decision making and risk management.
    """
    
    def __init__(self, config_path: str = "GEN_unified_config.json"):
        """Initialize multi-timeframe strategy"""
        self.config = self._load_config(config_path)
        self.timeframes = [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
        self.timeframe_weights = self._initialize_timeframe_weights()
        self.data_cache = {}
        self.signal_history = {}
        
        # Strategy parameters from config
        self.confluence_threshold = self.config.get("multi_timeframe", {}).get("confluence_threshold", 0.6)
        self.max_timeframes = self.config.get("multi_timeframe", {}).get("max_timeframes", 6)
        self.signal_decay_hours = self.config.get("multi_timeframe", {}).get("signal_decay_hours", 4)
        
        print("✅ Multi-Timeframe Strategy Engine initialized")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file not found: {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "multi_timeframe": {
                "confluence_threshold": 0.6,
                "max_timeframes": 6,
                "signal_decay_hours": 4,
                "timeframe_weights": {
                    "M1": 0.1,
                    "M5": 0.15,
                    "M15": 0.2,
                    "H1": 0.25,
                    "H4": 0.3,
                    "D1": 0.35
                },
                "indicators": {
                    "rsi_period": 14,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9,
                    "bb_period": 20,
                    "bb_std": 2,
                    "atr_period": 14
                }
            }
        }
    
    def _initialize_timeframe_weights(self) -> Dict[TimeFrame, float]:
        """Initialize timeframe importance weights"""
        default_weights = {
            TimeFrame.M1: 0.1,   # Short-term noise
            TimeFrame.M5: 0.15,  # Entry timing
            TimeFrame.M15: 0.2,  # Short-term trend
            TimeFrame.H1: 0.25,  # Medium-term trend
            TimeFrame.H4: 0.3,   # Strong trend
            TimeFrame.D1: 0.35   # Primary trend
        }
        
        config_weights = self.config.get("multi_timeframe", {}).get("timeframe_weights", {})
        
        # Update with config values if available
        for tf, weight in config_weights.items():
            if hasattr(TimeFrame, tf):
                default_weights[getattr(TimeFrame, tf)] = weight
        
        return default_weights
    
    def load_data(self, symbol: str, data_path: str = None) -> bool:
        """Load minute data for a symbol"""
        try:
            if data_path is None:
                data_path = f"CSVdata/raw/GEN_{symbol}_M1_1month.csv"
            
            if not os.path.exists(data_path):
                print(f"❌ Data file not found: {data_path}")
                return False
            
            # Load M1 data
            df = pd.read_csv(data_path)
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            
            # Generate higher timeframes
            timeframe_data = {}
            timeframe_data[TimeFrame.M1] = df
            
            # Create higher timeframes using OHLC resampling
            for tf in [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]:
                resampled = df.resample(tf.value).agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'tick_volume': 'sum',
                    'spread': 'mean',
                    'real_volume': 'sum'
                }).dropna()
                
                timeframe_data[tf] = resampled
            
            self.data_cache[symbol] = timeframe_data
            
            print(f"✅ Loaded {symbol} data across {len(timeframe_data)} timeframes")
            for tf, data in timeframe_data.items():
                print(f"   {tf.name}: {len(data)} bars")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading data for {symbol}: {e}")
            return False
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for a dataset"""
        df = data.copy()
        
        # Get parameters from config
        indicators_config = self.config.get("multi_timeframe", {}).get("indicators", {})
        rsi_period = indicators_config.get("rsi_period", 14)
        macd_fast = indicators_config.get("macd_fast", 12)
        macd_slow = indicators_config.get("macd_slow", 26)
        macd_signal = indicators_config.get("macd_signal", 9)
        bb_period = indicators_config.get("bb_period", 20)
        bb_std = indicators_config.get("bb_std", 2)
        atr_period = indicators_config.get("atr_period", 14)
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = df['close'].ewm(span=macd_fast).mean()
        ema_slow = df['close'].ewm(span=macd_slow).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=macd_signal).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=bb_period).mean()
        std = df['close'].rolling(window=bb_period).std()
        df['bb_upper'] = df['bb_middle'] + (std * bb_std)
        df['bb_lower'] = df['bb_middle'] - (std * bb_std)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # ATR (Average True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=atr_period).mean()
        df['atr_percent'] = df['atr'] / df['close']
        
        # Simple Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # Price momentum
        df['momentum_1'] = df['close'] / df['close'].shift(1) - 1
        df['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20'] = df['close'] / df['close'].shift(20) - 1
        
        return df
    
    def generate_timeframe_signal(self, symbol: str, timeframe: TimeFrame, 
                                 current_time: datetime = None) -> TimeframeSignal:
        """Generate trading signal for a specific timeframe"""
        
        if symbol not in self.data_cache:
            raise ValueError(f"Data not loaded for symbol: {symbol}")
        
        if timeframe not in self.data_cache[symbol]:
            raise ValueError(f"Timeframe {timeframe.name} not available for {symbol}")
        
        # Get data for this timeframe
        data = self.data_cache[symbol][timeframe]
        
        # Calculate indicators
        df = self.calculate_technical_indicators(data)
        
        # Get latest values (or at specific time if provided)
        if current_time:
            # Find closest time
            idx = df.index.get_indexer([current_time], method='nearest')[0]
            latest = df.iloc[idx]
            signal_time = df.index[idx]
        else:
            latest = df.iloc[-1]
            signal_time = df.index[-1]
        
        # Signal generation logic
        signals = []
        indicators = {}
        
        # RSI signals
        if latest['rsi'] < 30:
            signals.append(1)  # Oversold - Buy signal
            indicators['rsi_signal'] = 1
        elif latest['rsi'] > 70:
            signals.append(-1)  # Overbought - Sell signal
            indicators['rsi_signal'] = -1
        else:
            indicators['rsi_signal'] = 0
        
        indicators['rsi_value'] = latest['rsi']
        
        # MACD signals
        if latest['macd'] > latest['macd_signal'] and latest['macd_histogram'] > 0:
            signals.append(1)  # Bullish MACD
            indicators['macd_signal'] = 1
        elif latest['macd'] < latest['macd_signal'] and latest['macd_histogram'] < 0:
            signals.append(-1)  # Bearish MACD
            indicators['macd_signal'] = -1
        else:
            indicators['macd_signal'] = 0
        
        indicators['macd_value'] = latest['macd']
        indicators['macd_histogram'] = latest['macd_histogram']
        
        # Bollinger Band signals
        if latest['bb_position'] < 0.2:
            signals.append(1)  # Near lower band - Buy
            indicators['bb_signal'] = 1
        elif latest['bb_position'] > 0.8:
            signals.append(-1)  # Near upper band - Sell
            indicators['bb_signal'] = -1
        else:
            indicators['bb_signal'] = 0
        
        indicators['bb_position'] = latest['bb_position']
        indicators['bb_width'] = latest['bb_width']
        
        # Moving Average signals
        if latest['close'] > latest['sma_20'] > latest['sma_50']:
            signals.append(1)  # Bullish MA alignment
            indicators['ma_signal'] = 1
        elif latest['close'] < latest['sma_20'] < latest['sma_50']:
            signals.append(-1)  # Bearish MA alignment
            indicators['ma_signal'] = -1
        else:
            indicators['ma_signal'] = 0
        
        # Momentum signals
        if latest['momentum_20'] > 0.02:  # Strong upward momentum
            signals.append(1)
            indicators['momentum_signal'] = 1
        elif latest['momentum_20'] < -0.02:  # Strong downward momentum
            signals.append(-1)
            indicators['momentum_signal'] = -1
        else:
            indicators['momentum_signal'] = 0
        
        indicators['momentum_20'] = latest['momentum_20']
        indicators['atr_percent'] = latest['atr_percent']
        
        # Aggregate signals
        signal_sum = sum(signals)
        signal_count = len(signals)
        
        # Determine direction and strength
        if signal_sum >= 3:
            direction = MarketDirection.STRONG_BUY
            strength = SignalStrength.VERY_STRONG
        elif signal_sum >= 2:
            direction = MarketDirection.BUY
            strength = SignalStrength.STRONG
        elif signal_sum >= 1:
            direction = MarketDirection.BUY
            strength = SignalStrength.WEAK
        elif signal_sum <= -3:
            direction = MarketDirection.STRONG_SELL
            strength = SignalStrength.VERY_STRONG
        elif signal_sum <= -2:
            direction = MarketDirection.SELL
            strength = SignalStrength.STRONG
        elif signal_sum <= -1:
            direction = MarketDirection.SELL
            strength = SignalStrength.WEAK
        else:
            direction = MarketDirection.NEUTRAL
            strength = SignalStrength.NEUTRAL
        
        # Calculate confidence based on indicator agreement
        confidence = abs(signal_sum) / max(signal_count, 1)
        
        return TimeframeSignal(
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            confidence=confidence,
            indicators=indicators,
            timestamp=signal_time,
            price=latest['close']
        )
    
    def calculate_confluence_signal(self, symbol: str, current_time: datetime = None) -> ConfluentSignal:
        """Calculate confluent signal across all timeframes"""
        
        if symbol not in self.data_cache:
            raise ValueError(f"Data not loaded for symbol: {symbol}")
        
        # Generate signals for all timeframes
        timeframe_signals = []
        for tf in self.timeframes:
            if tf in self.data_cache[symbol]:
                try:
                    signal = self.generate_timeframe_signal(symbol, tf, current_time)
                    timeframe_signals.append(signal)
                except Exception as e:
                    print(f"⚠️  Error generating signal for {tf.name}: {e}")
        
        if not timeframe_signals:
            raise ValueError(f"No valid signals generated for {symbol}")
        
        # Calculate weighted consensus
        weighted_direction = 0
        total_weight = 0
        agreeing_timeframes = 0
        
        for signal in timeframe_signals:
            weight = self.timeframe_weights.get(signal.timeframe, 0.1)
            direction_value = signal.direction.value
            confidence = signal.confidence
            
            # Weight by timeframe importance and signal confidence
            adjusted_weight = weight * confidence
            weighted_direction += direction_value * adjusted_weight
            total_weight += adjusted_weight
            
            # Count agreeing timeframes (same direction)
            if abs(direction_value) > 0:
                agreeing_timeframes += 1
        
        # Normalize weighted direction
        if total_weight > 0:
            normalized_direction = weighted_direction / total_weight
        else:
            normalized_direction = 0
        
        # Determine overall direction
        if normalized_direction >= 1.5:
            overall_direction = MarketDirection.STRONG_BUY
        elif normalized_direction >= 0.5:
            overall_direction = MarketDirection.BUY
        elif normalized_direction <= -1.5:
            overall_direction = MarketDirection.STRONG_SELL
        elif normalized_direction <= -0.5:
            overall_direction = MarketDirection.SELL
        else:
            overall_direction = MarketDirection.NEUTRAL
        
        # Calculate confluence score (0-1)
        confluence_score = agreeing_timeframes / len(timeframe_signals)
        
        # Calculate overall signal strength
        overall_strength = min(abs(normalized_direction), 1.0)
        
        # Determine recommended action and risk level
        if confluence_score >= self.confluence_threshold and overall_strength >= 0.6:
            if overall_direction.value > 0:
                recommended_action = "STRONG_BUY" if overall_strength >= 0.8 else "BUY"
            else:
                recommended_action = "STRONG_SELL" if overall_strength >= 0.8 else "SELL"
            
            risk_level = "LOW" if confluence_score >= 0.8 else "MEDIUM"
            position_size_multiplier = confluence_score * overall_strength
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
    
    def analyze_symbol(self, symbol: str, current_time: datetime = None) -> ConfluentSignal:
        """Complete analysis for a symbol"""
        try:
            # Load data if not already cached
            if symbol not in self.data_cache:
                if not self.load_data(symbol):
                    raise ValueError(f"Failed to load data for {symbol}")
            
            # Generate confluence signal
            confluence_signal = self.calculate_confluence_signal(symbol, current_time)
            
            # Store in history
            if symbol not in self.signal_history:
                self.signal_history[symbol] = []
            
            self.signal_history[symbol].append(confluence_signal)
            
            return confluence_signal
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            raise
    
    def analyze_multiple_symbols(self, symbols: List[str], 
                                current_time: datetime = None) -> Dict[str, ConfluentSignal]:
        """Analyze multiple symbols simultaneously"""
        results = {}
        
        print(f"🔍 MULTI-TIMEFRAME ANALYSIS")
        print(f"=" * 60)
        print(f"Analyzing {len(symbols)} symbols across {len(self.timeframes)} timeframes")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n📊 Analyzing {symbol} ({i}/{len(symbols)})...")
            
            try:
                signal = self.analyze_symbol(symbol, current_time)
                results[symbol] = signal
                
                # Display results
                direction_icon = self._get_direction_icon(signal.overall_direction)
                risk_color = self._get_risk_color(signal.risk_level)
                
                print(f"   {direction_icon} {signal.recommended_action}")
                print(f"   📈 Strength: {signal.overall_strength:.2f} | Confluence: {signal.confluence_score:.2f}")
                print(f"   {risk_color} Risk: {signal.risk_level} | Size: {signal.position_size_multiplier:.2f}")
                
            except Exception as e:
                print(f"   ❌ Analysis failed: {e}")
                results[symbol] = None
        
        print(f"\n" + "=" * 60)
        print(f"📊 ANALYSIS COMPLETE: {len([r for r in results.values() if r])} successful")
        
        return results
    
    def _get_direction_icon(self, direction: MarketDirection) -> str:
        """Get icon for market direction"""
        icons = {
            MarketDirection.STRONG_BUY: "🟢🚀",
            MarketDirection.BUY: "🟢📈",
            MarketDirection.NEUTRAL: "⚪➡️",
            MarketDirection.SELL: "🔴📉",
            MarketDirection.STRONG_SELL: "🔴💥"
        }
        return icons.get(direction, "⚪")
    
    def _get_risk_color(self, risk_level: str) -> str:
        """Get color for risk level"""
        colors = {
            "LOW": "🟢",
            "MEDIUM": "🟡",
            "HIGH": "🔴"
        }
        return colors.get(risk_level, "⚪")
    
    def generate_detailed_report(self, symbol: str, confluence_signal: ConfluentSignal) -> str:
        """Generate detailed analysis report for a symbol"""
        report = []
        report.append(f"📊 MULTI-TIMEFRAME ANALYSIS: {symbol}")
        report.append("=" * 60)
        
        # Overall signal
        direction_icon = self._get_direction_icon(confluence_signal.overall_direction)
        risk_color = self._get_risk_color(confluence_signal.risk_level)
        
        report.append(f"🎯 OVERALL SIGNAL: {direction_icon} {confluence_signal.recommended_action}")
        report.append(f"📈 Strength: {confluence_signal.overall_strength:.2f}")
        report.append(f"🎯 Confluence: {confluence_signal.confluence_score:.2f}")
        report.append(f"{risk_color} Risk Level: {confluence_signal.risk_level}")
        report.append(f"📊 Position Size: {confluence_signal.position_size_multiplier:.2f}x")
        
        # Timeframe breakdown
        report.append("\n📊 TIMEFRAME BREAKDOWN:")
        report.append("-" * 40)
        
        for tf_signal in confluence_signal.timeframe_signals:
            direction_icon = self._get_direction_icon(tf_signal.direction)
            weight = self.timeframe_weights.get(tf_signal.timeframe, 0.1)
            
            report.append(f"{tf_signal.timeframe.name:>4}: {direction_icon} "
                        f"Strength: {tf_signal.strength.value:.2f} | "
                        f"Confidence: {tf_signal.confidence:.2f} | "
                        f"Weight: {weight:.2f}")
        
        # Key indicators
        report.append("\n🔍 KEY INDICATORS:")
        report.append("-" * 40)
        
        # Get H1 indicators as representative
        h1_signals = [s for s in confluence_signal.timeframe_signals if s.timeframe == TimeFrame.H1]
        if h1_signals:
            indicators = h1_signals[0].indicators
            report.append(f"RSI: {indicators.get('rsi_value', 0):.1f}")
            report.append(f"MACD: {indicators.get('macd_value', 0):.6f}")
            report.append(f"BB Position: {indicators.get('bb_position', 0):.2f}")
            report.append(f"Momentum (20): {indicators.get('momentum_20', 0):.3f}")
            report.append(f"ATR %: {indicators.get('atr_percent', 0):.3f}")
        
        return "\n".join(report)

def main():
    """Main execution for testing"""
    print("🚀 MULTI-TIMEFRAME STRATEGY ENGINE")
    print("=" * 60)
    
    # Initialize strategy
    strategy = MultiTimeframeStrategy()
    
    # Test symbols (high quality data)
    test_symbols = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"]
    
    # Analyze symbols
    results = strategy.analyze_multiple_symbols(test_symbols)
    
    # Generate detailed reports
    print("\n" + "=" * 80)
    print("📋 DETAILED ANALYSIS REPORTS")
    print("=" * 80)
    
    for symbol, signal in results.items():
        if signal:
            print(strategy.generate_detailed_report(symbol, signal))
            print()

if __name__ == "__main__":
    main()
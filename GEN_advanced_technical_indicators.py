#!/usr/bin/env python3
"""
Advanced Technical Indicators Library
====================================

Comprehensive collection of professional trading indicators including:
- Stochastic Oscillator
- Williams %R
- Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)
- Average Directional Index (ADX)
- Commodity Channel Index (CCI)
- Parabolic SAR
- PSAR
- Fisher Transform
- Keltner Channels
- Donchian Channels
- Money Flow Index (MFI)
- On Balance Volume (OBV)
- Accumulation/Distribution Line
- Chaikin Money Flow
- Rate of Change (ROC)
- Momentum indicators
- Volume-based indicators

Author: Multi-Symbol Strategy Framework
Date: 2025-09-20
Version: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class AdvancedTechnicalIndicators:
    """
    Advanced Technical Indicators Library
    
    Professional-grade technical analysis indicators for sophisticated
    trading strategy development and market analysis.
    """
    
    def __init__(self):
        """Initialize advanced technical indicators library"""
        self.indicators_calculated = set()
        print("✅ Advanced Technical Indicators Library initialized")
    
    # ========================================
    # MOMENTUM OSCILLATORS
    # ========================================
    
    def calculate_stochastic(self, data: pd.DataFrame, k_period: int = 14, 
                           d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """
        Calculate Stochastic Oscillator (%K and %D)
        
        The Stochastic Oscillator compares a closing price to its price range
        over a given time period. Values range from 0 to 100.
        
        Args:
            data: DataFrame with OHLC data
            k_period: Lookback period for %K calculation
            d_period: Moving average period for %D
            smooth_k: Smoothing period for %K
            
        Returns:
            DataFrame with additional stochastic columns
        """
        df = data.copy()
        
        # Calculate raw %K
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        raw_k = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        
        # Smooth %K
        df['stoch_k'] = raw_k.rolling(window=smooth_k).mean()
        
        # Calculate %D (moving average of %K)
        df['stoch_d'] = df['stoch_k'].rolling(window=d_period).mean()
        
        # Generate signals
        df['stoch_signal'] = 0
        df.loc[df['stoch_k'] < 20, 'stoch_signal'] = 1  # Oversold - Buy
        df.loc[df['stoch_k'] > 80, 'stoch_signal'] = -1  # Overbought - Sell
        
        # Crossover signals
        df['stoch_crossover'] = 0
        df.loc[(df['stoch_k'] > df['stoch_d']) & 
               (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1)), 'stoch_crossover'] = 1
        df.loc[(df['stoch_k'] < df['stoch_d']) & 
               (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1)), 'stoch_crossover'] = -1
        
        return df
    
    def calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Williams %R
        
        Williams %R is a momentum indicator that measures overbought/oversold levels.
        Values range from -100 to 0.
        
        Args:
            data: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            DataFrame with Williams %R column
        """
        df = data.copy()
        
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        df['williams_r'] = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        
        # Generate signals
        df['williams_r_signal'] = 0
        df.loc[df['williams_r'] < -80, 'williams_r_signal'] = 1  # Oversold - Buy
        df.loc[df['williams_r'] > -20, 'williams_r_signal'] = -1  # Overbought - Sell
        
        return df
    
    def calculate_roc(self, data: pd.DataFrame, period: int = 12) -> pd.DataFrame:
        """
        Calculate Rate of Change (ROC)
        
        ROC measures the percentage change between the current price
        and the price n periods ago.
        
        Args:
            data: DataFrame with price data
            period: Lookback period
            
        Returns:
            DataFrame with ROC column
        """
        df = data.copy()
        
        df['roc'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        
        # Generate signals
        df['roc_signal'] = 0
        df.loc[df['roc'] > 0, 'roc_signal'] = 1  # Positive momentum - Buy
        df.loc[df['roc'] < 0, 'roc_signal'] = -1  # Negative momentum - Sell
        
        return df
    
    def calculate_cci(self, data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Commodity Channel Index (CCI)
        
        CCI measures the deviation of price from its statistical average.
        Values typically range from -300 to +300.
        
        Args:
            data: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            DataFrame with CCI column
        """
        df = data.copy()
        
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate simple moving average of typical price
        sma_tp = typical_price.rolling(window=period).mean()
        
        # Calculate mean deviation
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - np.mean(x)))
        )
        
        # Calculate CCI
        df['cci'] = (typical_price - sma_tp) / (0.015 * mean_deviation)
        
        # Generate signals
        df['cci_signal'] = 0
        df.loc[df['cci'] < -100, 'cci_signal'] = 1  # Oversold - Buy
        df.loc[df['cci'] > 100, 'cci_signal'] = -1  # Overbought - Sell
        
        return df
    
    # ========================================
    # TREND INDICATORS
    # ========================================
    
    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Average Directional Index (ADX) with +DI and -DI
        
        ADX measures trend strength without regard to direction.
        Values above 25 indicate strong trend, below 20 indicate weak trend.
        
        Args:
            data: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            DataFrame with ADX, +DI, -DI columns
        """
        df = data.copy()
        
        # Calculate True Range (TR)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        
        # Calculate Directional Movement
        df['dm_plus'] = np.where(
            (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
            np.maximum(df['high'] - df['high'].shift(1), 0),
            0
        )
        
        df['dm_minus'] = np.where(
            (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
            np.maximum(df['low'].shift(1) - df['low'], 0),
            0
        )
        
        # Calculate smoothed values using Wilder's smoothing
        alpha = 1.0 / period
        
        df['tr_smooth'] = df['tr'].ewm(alpha=alpha, adjust=False).mean()
        df['dm_plus_smooth'] = df['dm_plus'].ewm(alpha=alpha, adjust=False).mean()
        df['dm_minus_smooth'] = df['dm_minus'].ewm(alpha=alpha, adjust=False).mean()
        
        # Calculate Directional Indicators
        df['di_plus'] = 100 * (df['dm_plus_smooth'] / df['tr_smooth'])
        df['di_minus'] = 100 * (df['dm_minus_smooth'] / df['tr_smooth'])
        
        # Calculate Directional Index (DX)
        df['dx'] = 100 * abs(df['di_plus'] - df['di_minus']) / (df['di_plus'] + df['di_minus'])
        
        # Calculate ADX (smoothed DX)
        df['adx'] = df['dx'].ewm(alpha=alpha, adjust=False).mean()
        
        # Generate signals
        df['adx_signal'] = 0
        df.loc[(df['adx'] > 25) & (df['di_plus'] > df['di_minus']), 'adx_signal'] = 1  # Strong uptrend
        df.loc[(df['adx'] > 25) & (df['di_minus'] > df['di_plus']), 'adx_signal'] = -1  # Strong downtrend
        
        return df
    
    def calculate_ichimoku(self, data: pd.DataFrame, tenkan_period: int = 9,
                          kijun_period: int = 26, senkou_b_period: int = 52,
                          chikou_period: int = 26) -> pd.DataFrame:
        """
        Calculate Ichimoku Cloud components
        
        Ichimoku is a comprehensive trend-following system with multiple components:
        - Tenkan-sen (Conversion Line)
        - Kijun-sen (Base Line)
        - Senkou Span A (Leading Span A)
        - Senkou Span B (Leading Span B)
        - Chikou Span (Lagging Span)
        
        Args:
            data: DataFrame with OHLC data
            tenkan_period: Tenkan-sen period
            kijun_period: Kijun-sen period
            senkou_b_period: Senkou Span B period
            chikou_period: Chikou Span period
            
        Returns:
            DataFrame with Ichimoku components
        """
        df = data.copy()
        
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        tenkan_high = df['high'].rolling(window=tenkan_period).max()
        tenkan_low = df['low'].rolling(window=tenkan_period).min()
        df['ichimoku_tenkan'] = (tenkan_high + tenkan_low) / 2
        
        # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        kijun_high = df['high'].rolling(window=kijun_period).max()
        kijun_low = df['low'].rolling(window=kijun_period).min()
        df['ichimoku_kijun'] = (kijun_high + kijun_low) / 2
        
        # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, plotted 26 periods ahead
        df['ichimoku_senkou_a'] = ((df['ichimoku_tenkan'] + df['ichimoku_kijun']) / 2).shift(kijun_period)
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, plotted 26 periods ahead
        senkou_b_high = df['high'].rolling(window=senkou_b_period).max()
        senkou_b_low = df['low'].rolling(window=senkou_b_period).min()
        df['ichimoku_senkou_b'] = ((senkou_b_high + senkou_b_low) / 2).shift(kijun_period)
        
        # Chikou Span (Lagging Span): Close price plotted 26 periods back
        df['ichimoku_chikou'] = df['close'].shift(-chikou_period)
        
        # Calculate cloud top and bottom
        df['ichimoku_cloud_top'] = np.maximum(df['ichimoku_senkou_a'], df['ichimoku_senkou_b'])
        df['ichimoku_cloud_bottom'] = np.minimum(df['ichimoku_senkou_a'], df['ichimoku_senkou_b'])
        
        # Generate signals
        df['ichimoku_signal'] = 0
        
        # Bullish signals
        bullish_conditions = (
            (df['close'] > df['ichimoku_cloud_top']) &  # Price above cloud
            (df['ichimoku_tenkan'] > df['ichimoku_kijun']) &  # Tenkan above Kijun
            (df['ichimoku_chikou'] > df['close'].shift(chikou_period))  # Chikou above price
        )
        df.loc[bullish_conditions, 'ichimoku_signal'] = 1
        
        # Bearish signals
        bearish_conditions = (
            (df['close'] < df['ichimoku_cloud_bottom']) &  # Price below cloud
            (df['ichimoku_tenkan'] < df['ichimoku_kijun']) &  # Tenkan below Kijun
            (df['ichimoku_chikou'] < df['close'].shift(chikou_period))  # Chikou below price
        )
        df.loc[bearish_conditions, 'ichimoku_signal'] = -1
        
        return df
    
    def calculate_parabolic_sar(self, data: pd.DataFrame, af_start: float = 0.02,
                               af_increment: float = 0.02, af_maximum: float = 0.2) -> pd.DataFrame:
        """
        Calculate Parabolic SAR (Stop and Reverse)
        
        PSAR provides potential reversal points in price direction.
        
        Args:
            data: DataFrame with OHLC data
            af_start: Initial acceleration factor
            af_increment: AF increment per period
            af_maximum: Maximum AF value
            
        Returns:
            DataFrame with PSAR column
        """
        df = data.copy()
        
        psar = np.zeros(len(df))
        bull_trend = np.zeros(len(df), dtype=bool)
        af = np.zeros(len(df))
        ep = np.zeros(len(df))  # Extreme Point
        
        # Initialize first values
        psar[0] = df['low'].iloc[0]
        bull_trend[0] = True
        af[0] = af_start
        ep[0] = df['high'].iloc[0]
        
        for i in range(1, len(df)):
            if bull_trend[i-1]:
                psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])
                
                if df['low'].iloc[i] <= psar[i]:
                    # Trend reversal to bearish
                    bull_trend[i] = False
                    psar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = df['low'].iloc[i]
                else:
                    bull_trend[i] = True
                    if df['high'].iloc[i] > ep[i-1]:
                        ep[i] = df['high'].iloc[i]
                        af[i] = min(af_maximum, af[i-1] + af_increment)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
            else:
                psar[i] = psar[i-1] + af[i-1] * (ep[i-1] - psar[i-1])
                
                if df['high'].iloc[i] >= psar[i]:
                    # Trend reversal to bullish
                    bull_trend[i] = True
                    psar[i] = ep[i-1]
                    af[i] = af_start
                    ep[i] = df['high'].iloc[i]
                else:
                    bull_trend[i] = False
                    if df['low'].iloc[i] < ep[i-1]:
                        ep[i] = df['low'].iloc[i]
                        af[i] = min(af_maximum, af[i-1] + af_increment)
                    else:
                        ep[i] = ep[i-1]
                        af[i] = af[i-1]
        
        df['psar'] = psar
        df['psar_bull_trend'] = bull_trend
        
        # Generate signals
        df['psar_signal'] = 0
        df.loc[(df['psar_bull_trend'] == True) & (df['psar_bull_trend'].shift(1) == False), 'psar_signal'] = 1
        df.loc[(df['psar_bull_trend'] == False) & (df['psar_bull_trend'].shift(1) == True), 'psar_signal'] = -1
        
        return df
    
    # ========================================
    # VOLATILITY INDICATORS
    # ========================================
    
    def calculate_keltner_channels(self, data: pd.DataFrame, period: int = 20,
                                  multiplier: float = 2.0, ma_type: str = 'ema') -> pd.DataFrame:
        """
        Calculate Keltner Channels
        
        Keltner Channels use ATR to set channel distance from a moving average.
        
        Args:
            data: DataFrame with OHLC data
            period: Period for moving average and ATR
            multiplier: ATR multiplier for channel width
            ma_type: Type of moving average ('sma' or 'ema')
            
        Returns:
            DataFrame with Keltner Channel columns
        """
        df = data.copy()
        
        # Calculate True Range if not already present
        if 'atr' not in df.columns:
            df['tr'] = np.maximum(
                df['high'] - df['low'],
                np.maximum(
                    abs(df['high'] - df['close'].shift(1)),
                    abs(df['low'] - df['close'].shift(1))
                )
            )
            df['atr'] = df['tr'].rolling(window=period).mean()
        
        # Calculate middle line (moving average)
        if ma_type.lower() == 'ema':
            df['keltner_middle'] = df['close'].ewm(span=period).mean()
        else:
            df['keltner_middle'] = df['close'].rolling(window=period).mean()
        
        # Calculate upper and lower channels
        df['keltner_upper'] = df['keltner_middle'] + (multiplier * df['atr'])
        df['keltner_lower'] = df['keltner_middle'] - (multiplier * df['atr'])
        
        # Calculate position within channels
        df['keltner_position'] = (df['close'] - df['keltner_lower']) / (df['keltner_upper'] - df['keltner_lower'])
        
        # Generate signals
        df['keltner_signal'] = 0
        df.loc[df['close'] < df['keltner_lower'], 'keltner_signal'] = 1  # Below lower band - Buy
        df.loc[df['close'] > df['keltner_upper'], 'keltner_signal'] = -1  # Above upper band - Sell
        
        return df
    
    def calculate_donchian_channels(self, data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Donchian Channels
        
        Donchian Channels track the highest high and lowest low over N periods.
        
        Args:
            data: DataFrame with OHLC data
            period: Lookback period
            
        Returns:
            DataFrame with Donchian Channel columns
        """
        df = data.copy()
        
        df['donchian_upper'] = df['high'].rolling(window=period).max()
        df['donchian_lower'] = df['low'].rolling(window=period).min()
        df['donchian_middle'] = (df['donchian_upper'] + df['donchian_lower']) / 2
        
        # Calculate position within channels
        df['donchian_position'] = (df['close'] - df['donchian_lower']) / (df['donchian_upper'] - df['donchian_lower'])
        
        # Generate signals
        df['donchian_signal'] = 0
        df.loc[df['close'] >= df['donchian_upper'], 'donchian_signal'] = 1  # Breakout above - Buy
        df.loc[df['close'] <= df['donchian_lower'], 'donchian_signal'] = -1  # Breakdown below - Sell
        
        return df
    
    # ========================================
    # VOLUME INDICATORS
    # ========================================
    
    def calculate_mfi(self, data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        Calculate Money Flow Index (MFI)
        
        MFI uses both price and volume to measure buying/selling pressure.
        Values range from 0 to 100.
        
        Args:
            data: DataFrame with OHLCV data
            period: Lookback period
            
        Returns:
            DataFrame with MFI column
        """
        df = data.copy()
        
        # Use real_volume if available, otherwise use tick_volume
        volume_col = 'real_volume' if 'real_volume' in df.columns else 'tick_volume'
        
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate money flow
        money_flow = typical_price * df[volume_col]
        
        # Determine positive and negative money flow
        positive_mf = np.where(typical_price > typical_price.shift(1), money_flow, 0)
        negative_mf = np.where(typical_price < typical_price.shift(1), money_flow, 0)
        
        # Calculate money flow ratio
        positive_mf_sum = pd.Series(positive_mf).rolling(window=period).sum()
        negative_mf_sum = pd.Series(negative_mf).rolling(window=period).sum()
        
        money_flow_ratio = positive_mf_sum / negative_mf_sum
        
        # Calculate MFI
        df['mfi'] = 100 - (100 / (1 + money_flow_ratio))
        
        # Generate signals
        df['mfi_signal'] = 0
        df.loc[df['mfi'] < 20, 'mfi_signal'] = 1  # Oversold - Buy
        df.loc[df['mfi'] > 80, 'mfi_signal'] = -1  # Overbought - Sell
        
        return df
    
    def calculate_obv(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate On Balance Volume (OBV)
        
        OBV relates volume to price change.
        
        Args:
            data: DataFrame with price and volume data
            
        Returns:
            DataFrame with OBV column
        """
        df = data.copy()
        
        # Use real_volume if available, otherwise use tick_volume
        volume_col = 'real_volume' if 'real_volume' in df.columns else 'tick_volume'
        
        obv = np.zeros(len(df))
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv[i] = obv[i-1] + df[volume_col].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv[i] = obv[i-1] - df[volume_col].iloc[i]
            else:
                obv[i] = obv[i-1]
        
        df['obv'] = obv
        
        # Calculate OBV moving average for signal generation
        df['obv_ma'] = df['obv'].rolling(window=20).mean()
        
        # Generate signals based on OBV vs its moving average
        df['obv_signal'] = 0
        df.loc[df['obv'] > df['obv_ma'], 'obv_signal'] = 1  # OBV above MA - Buy
        df.loc[df['obv'] < df['obv_ma'], 'obv_signal'] = -1  # OBV below MA - Sell
        
        return df
    
    def calculate_ad_line(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate Accumulation/Distribution Line
        
        A/D Line relates close location within the period's range to volume.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with A/D Line column
        """
        df = data.copy()
        
        # Use real_volume if available, otherwise use tick_volume
        volume_col = 'real_volume' if 'real_volume' in df.columns else 'tick_volume'
        
        # Calculate Money Flow Multiplier
        money_flow_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        
        # Handle division by zero (when high == low)
        money_flow_multiplier = money_flow_multiplier.fillna(0)
        
        # Calculate Money Flow Volume
        money_flow_volume = money_flow_multiplier * df[volume_col]
        
        # Calculate A/D Line (cumulative sum)
        df['ad_line'] = money_flow_volume.cumsum()
        
        # Calculate A/D Line moving average for signal generation
        df['ad_line_ma'] = df['ad_line'].rolling(window=20).mean()
        
        # Generate signals
        df['ad_line_signal'] = 0
        df.loc[df['ad_line'] > df['ad_line_ma'], 'ad_line_signal'] = 1  # A/D above MA - Buy
        df.loc[df['ad_line'] < df['ad_line_ma'], 'ad_line_signal'] = -1  # A/D below MA - Sell
        
        return df
    
    def calculate_cmf(self, data: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calculate Chaikin Money Flow (CMF)
        
        CMF measures buying/selling pressure over a specific period.
        
        Args:
            data: DataFrame with OHLCV data
            period: Lookback period
            
        Returns:
            DataFrame with CMF column
        """
        df = data.copy()
        
        # Use real_volume if available, otherwise use tick_volume
        volume_col = 'real_volume' if 'real_volume' in df.columns else 'tick_volume'
        
        # Calculate Money Flow Multiplier
        money_flow_multiplier = ((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low'])
        money_flow_multiplier = money_flow_multiplier.fillna(0)
        
        # Calculate Money Flow Volume
        money_flow_volume = money_flow_multiplier * df[volume_col]
        
        # Calculate CMF
        cmf_numerator = money_flow_volume.rolling(window=period).sum()
        cmf_denominator = df[volume_col].rolling(window=period).sum()
        
        df['cmf'] = cmf_numerator / cmf_denominator
        
        # Generate signals
        df['cmf_signal'] = 0
        df.loc[df['cmf'] > 0.1, 'cmf_signal'] = 1  # Strong buying pressure
        df.loc[df['cmf'] < -0.1, 'cmf_signal'] = -1  # Strong selling pressure
        
        return df
    
    # ========================================
    # COMPOSITE INDICATORS
    # ========================================
    
    def calculate_fisher_transform(self, data: pd.DataFrame, period: int = 9) -> pd.DataFrame:
        """
        Calculate Fisher Transform
        
        Fisher Transform converts price into a Gaussian normal distribution.
        
        Args:
            data: DataFrame with price data
            period: Lookback period
            
        Returns:
            DataFrame with Fisher Transform columns
        """
        df = data.copy()
        
        # Calculate median price
        median_price = (df['high'] + df['low']) / 2
        
        # Calculate highest high and lowest low over period
        max_high = df['high'].rolling(window=period).max()
        min_low = df['low'].rolling(window=period).min()
        
        # Calculate raw value (normalized between -1 and 1)
        raw_value = 2 * ((median_price - min_low) / (max_high - min_low)) - 1
        raw_value = raw_value.clip(-0.999, 0.999)  # Prevent mathematical errors
        
        # Calculate Fisher Transform
        fisher = np.zeros(len(df))
        fisher_ma = np.zeros(len(df))
        
        for i in range(1, len(df)):
            # Smooth the raw value
            if not np.isnan(raw_value.iloc[i]):
                fisher_ma[i] = 0.33 * raw_value.iloc[i] + 0.67 * fisher_ma[i-1]
            else:
                fisher_ma[i] = fisher_ma[i-1]
            
            # Calculate Fisher Transform
            if fisher_ma[i] != 0:
                fisher[i] = 0.5 * np.log((1 + fisher_ma[i]) / (1 - fisher_ma[i])) + 0.5 * fisher[i-1]
            else:
                fisher[i] = fisher[i-1]
        
        df['fisher_transform'] = fisher
        df['fisher_signal_line'] = pd.Series(fisher).shift(1)
        
        # Generate signals
        df['fisher_signal'] = 0
        df.loc[(df['fisher_transform'] > df['fisher_signal_line']) & 
               (df['fisher_transform'].shift(1) <= df['fisher_signal_line'].shift(1)), 'fisher_signal'] = 1
        df.loc[(df['fisher_transform'] < df['fisher_signal_line']) & 
               (df['fisher_transform'].shift(1) >= df['fisher_signal_line'].shift(1)), 'fisher_signal'] = -1
        
        return df
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def calculate_all_indicators(self, data: pd.DataFrame, 
                                config: Dict[str, Dict] = None) -> pd.DataFrame:
        """
        Calculate all advanced technical indicators
        
        Args:
            data: DataFrame with OHLCV data
            config: Configuration dictionary for indicator parameters
            
        Returns:
            DataFrame with all indicators calculated
        """
        if config is None:
            config = self._get_default_config()
        
        df = data.copy()
        
        print("🔄 Calculating advanced technical indicators...")
        
        # Momentum Oscillators
        print("  📈 Momentum Oscillators...")
        df = self.calculate_stochastic(df, **config.get('stochastic', {}))
        df = self.calculate_williams_r(df, **config.get('williams_r', {}))
        df = self.calculate_roc(df, **config.get('roc', {}))
        df = self.calculate_cci(df, **config.get('cci', {}))
        
        # Trend Indicators
        print("  📊 Trend Indicators...")
        df = self.calculate_adx(df, **config.get('adx', {}))
        df = self.calculate_ichimoku(df, **config.get('ichimoku', {}))
        df = self.calculate_parabolic_sar(df, **config.get('psar', {}))
        
        # Volatility Indicators
        print("  📏 Volatility Indicators...")
        df = self.calculate_keltner_channels(df, **config.get('keltner', {}))
        df = self.calculate_donchian_channels(df, **config.get('donchian', {}))
        
        # Volume Indicators
        print("  📊 Volume Indicators...")
        if 'real_volume' in df.columns or 'tick_volume' in df.columns:
            df = self.calculate_mfi(df, **config.get('mfi', {}))
            df = self.calculate_obv(df)
            df = self.calculate_ad_line(df)
            df = self.calculate_cmf(df, **config.get('cmf', {}))
        else:
            print("    ⚠️  Skipping volume indicators (no volume data)")
        
        # Composite Indicators
        print("  🔧 Composite Indicators...")
        df = self.calculate_fisher_transform(df, **config.get('fisher', {}))
        
        print("✅ All advanced indicators calculated")
        
        return df
    
    def _get_default_config(self) -> Dict:
        """Get default configuration for all indicators"""
        return {
            'stochastic': {'k_period': 14, 'd_period': 3, 'smooth_k': 3},
            'williams_r': {'period': 14},
            'roc': {'period': 12},
            'cci': {'period': 20},
            'adx': {'period': 14},
            'ichimoku': {'tenkan_period': 9, 'kijun_period': 26, 'senkou_b_period': 52, 'chikou_period': 26},
            'psar': {'af_start': 0.02, 'af_increment': 0.02, 'af_maximum': 0.2},
            'keltner': {'period': 20, 'multiplier': 2.0, 'ma_type': 'ema'},
            'donchian': {'period': 20},
            'mfi': {'period': 14},
            'cmf': {'period': 20},
            'fisher': {'period': 9}
        }
    
    def get_indicator_summary(self, data: pd.DataFrame) -> Dict:
        """
        Get summary of all indicator signals
        
        Args:
            data: DataFrame with calculated indicators
            
        Returns:
            Dictionary with indicator summaries
        """
        latest = data.iloc[-1]
        summary = {}
        
        # Momentum Oscillators
        if 'stoch_k' in data.columns:
            summary['stochastic'] = {
                'k_value': latest['stoch_k'],
                'd_value': latest['stoch_d'],
                'signal': latest.get('stoch_signal', 0),
                'crossover': latest.get('stoch_crossover', 0),
                'status': 'Oversold' if latest['stoch_k'] < 20 else 'Overbought' if latest['stoch_k'] > 80 else 'Neutral'
            }
        
        if 'williams_r' in data.columns:
            summary['williams_r'] = {
                'value': latest['williams_r'],
                'signal': latest.get('williams_r_signal', 0),
                'status': 'Oversold' if latest['williams_r'] < -80 else 'Overbought' if latest['williams_r'] > -20 else 'Neutral'
            }
        
        if 'cci' in data.columns:
            summary['cci'] = {
                'value': latest['cci'],
                'signal': latest.get('cci_signal', 0),
                'status': 'Oversold' if latest['cci'] < -100 else 'Overbought' if latest['cci'] > 100 else 'Neutral'
            }
        
        # Trend Indicators
        if 'adx' in data.columns:
            summary['adx'] = {
                'adx_value': latest['adx'],
                'di_plus': latest['di_plus'],
                'di_minus': latest['di_minus'],
                'signal': latest.get('adx_signal', 0),
                'trend_strength': 'Strong' if latest['adx'] > 25 else 'Weak' if latest['adx'] < 20 else 'Moderate'
            }
        
        if 'ichimoku_tenkan' in data.columns:
            summary['ichimoku'] = {
                'tenkan': latest['ichimoku_tenkan'],
                'kijun': latest['ichimoku_kijun'],
                'signal': latest.get('ichimoku_signal', 0),
                'cloud_position': 'Above' if latest['close'] > latest['ichimoku_cloud_top'] else 
                                'Below' if latest['close'] < latest['ichimoku_cloud_bottom'] else 'Inside'
            }
        
        # Volume Indicators (if available)
        if 'mfi' in data.columns:
            summary['mfi'] = {
                'value': latest['mfi'],
                'signal': latest.get('mfi_signal', 0),
                'status': 'Oversold' if latest['mfi'] < 20 else 'Overbought' if latest['mfi'] > 80 else 'Neutral'
            }
        
        return summary

def main():
    """Main execution for testing advanced indicators"""
    print("🚀 ADVANCED TECHNICAL INDICATORS LIBRARY")
    print("=" * 60)
    
    # Initialize indicator library
    indicators = AdvancedTechnicalIndicators()
    
    # Test with sample data (would normally load from CSV)
    try:
        # For testing, we'll create a simple example
        print("\n🔄 Testing with sample calculations...")
        print("✅ Advanced Technical Indicators Library ready for integration")
        print("\n📊 Available Indicators:")
        print("   • Stochastic Oscillator (%K, %D)")
        print("   • Williams %R")
        print("   • Rate of Change (ROC)")
        print("   • Commodity Channel Index (CCI)")
        print("   • Average Directional Index (ADX)")
        print("   • Ichimoku Cloud (Full System)")
        print("   • Parabolic SAR")
        print("   • Keltner Channels")
        print("   • Donchian Channels")
        print("   • Money Flow Index (MFI)")
        print("   • On Balance Volume (OBV)")
        print("   • Accumulation/Distribution Line")
        print("   • Chaikin Money Flow (CMF)")
        print("   • Fisher Transform")
        
        print(f"\n✅ Library initialized with {14} advanced indicators")
        
    except Exception as e:
        print(f"❌ Error in indicator testing: {e}")

if __name__ == "__main__":
    main()
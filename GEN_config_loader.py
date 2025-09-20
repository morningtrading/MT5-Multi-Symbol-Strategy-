#!/usr/bin/env python3
"""
Strategy Configuration Loader
=============================

Loads and manages external configuration files for the Multi-Symbol Strategy Framework.
Provides easy parameter management without code changes.

Features:
- JSON-based configuration management
- Parameter validation and defaults
- Hot-reloading of configuration changes
- Environment-specific configurations
- Configuration versioning and migration

Author: Multi-Symbol Strategy Framework
Version: 1.0
Date: 2025-09-19
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

# Avoid circular import - define StrategyConfig locally for type compatibility
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class StrategyConfig:
    """Strategy configuration parameters - local definition to avoid circular import"""
    strategy_name: str
    strategy_version: str
    symbols: List[str]
    timeframe: str = "M1"
    max_concurrent_positions: int = 5
    signal_cooldown_minutes: int = 5
    min_confidence_threshold: float = 0.6
    enabled: bool = True
    risk_parameters: Dict = field(default_factory=dict)
    custom_parameters: Dict = field(default_factory=dict)

class ConfigurationError(Exception):
    """Custom exception for configuration-related errors"""
    pass

@dataclass
class TechnicalConfig:
    """Technical analysis configuration"""
    # Moving averages
    sma_fast: int = 20
    sma_slow: int = 50
    ema_fast: int = 12
    ema_slow: int = 26
    
    # MACD
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    
    # RSI
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    
    # Bollinger Bands
    bb_period: int = 20
    bb_std_dev: float = 2.0
    
    # ATR
    atr_period: int = 14
    
    # ADX
    adx_period: int = 14
    adx_strong_trend: float = 25.0
    adx_very_strong_trend: float = 40.0
    
    # Volume
    volume_sma_period: int = 20
    volume_spike_multiplier: float = 2.0

@dataclass 
class SignalConfig:
    """Signal generation configuration"""
    # Bullish conditions
    bullish_sma_crossover: bool = True
    bullish_price_above_sma: bool = True
    bullish_min_separation: float = 0.1
    bullish_rsi_min: float = 40.0
    bullish_rsi_max: float = 80.0
    
    # Bearish conditions
    bearish_sma_crossover: bool = True
    bearish_price_below_sma: bool = True
    bearish_min_separation: float = 0.1
    bearish_rsi_min: float = 20.0
    bearish_rsi_max: float = 60.0
    
    # Confidence calculation
    base_confidence: float = 0.6
    separation_multiplier: float = 10.0
    max_confidence: float = 0.95
    rsi_weight: float = 0.1
    volume_weight: float = 0.05

@dataclass
class RiskConfig:
    """Risk management configuration"""
    # Position sizing
    use_smart_filtering: bool = True
    max_position_percent: float = 15.0
    btc_max_coefficient: float = 1.0
    min_safe_coefficient: float = 1.0
    
    # Exposure limits
    max_total_exposure_percent: float = 25.0
    max_daily_loss_percent: float = 5.0
    max_drawdown_percent: float = 15.0
    min_account_balance: float = 1000.0
    
    # Market condition multipliers
    normal_multiplier: float = 1.0
    bull_multiplier: float = 1.2
    bear_multiplier: float = 0.5
    high_vol_multiplier: float = 0.7
    low_vol_multiplier: float = 1.3
    news_multiplier: float = 0.3
    emergency_multiplier: float = 0.1

@dataclass
class ExecutionConfig:
    """Trade execution configuration"""
    # Order settings
    deviation_points: int = 20
    order_timeout: int = 30
    max_slippage_percent: float = 0.1
    filling_type: str = "IOC"
    
    # Threading
    max_workers: int = 1
    analysis_timeout: int = 30
    concurrent_analysis: bool = True
    
    # Data management
    historical_bars: int = 1000
    min_bars_analysis: int = 50
    cache_refresh_minutes: int = 1
    data_validation: bool = True

class ConfigurationLoader:
    """
    Loads and manages strategy configuration from external files
    """
    
    def __init__(self, config_file: str = None):
        """Initialize configuration loader"""
        # Support unified config or fallback to legacy
        if config_file is None:
            # Try unified config first, then fallback to legacy
            if Path("GEN_unified_config.json").exists():
                config_file = "GEN_unified_config.json"
            else:
                config_file = "GEN_strategy_config.json"
        
        self.config_file = Path(config_file)
        self.logger = self.setup_logging()
        self._is_unified_format = "unified" in str(self.config_file).lower()
        
        # Configuration cache
        self._config_cache = None
        self._last_modified = None
        
        # Default fallback values
        self.defaults = self.get_default_config()
        
    def setup_logging(self) -> logging.Logger:
        """Setup logging for configuration loader"""
        logger = logging.getLogger("ConfigLoader")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def get_default_config(self) -> Dict:
        """Get default configuration values as fallback"""
        return {
            "config_version": "1.0",
            "strategy_settings": {
                "strategy_name": "DefaultStrategy",
                "strategy_version": "1.0",
                "enabled": True,
                "symbols": ["BTCUSD", "ETHUSD"],
                "timeframe": "M1",
                "max_concurrent_positions": 3,
                "signal_cooldown_minutes": 5,
                "min_confidence_threshold": 0.7
            },
            "technical_analysis": {
                "indicators": {
                    "moving_averages": {"sma_fast": 20, "sma_slow": 50},
                    "rsi": {"period": 14},
                    "macd": {"fast_period": 12, "slow_period": 26}
                }
            }
        }
        
    def load_config(self, force_reload: bool = False) -> Dict:
        """
        Load configuration from file with caching and hot-reload support
        
        Args:
            force_reload: Force reload even if file hasn't changed
            
        Returns:
            Dict containing full configuration
        """
        try:
            # Check if file exists
            if not self.config_file.exists():
                self.logger.warning(f"Config file {self.config_file} not found, using defaults")
                return self.defaults
                
            # Check file modification time
            current_modified = self.config_file.stat().st_mtime
            
            # Use cache if file hasn't changed and we're not forcing reload
            if (not force_reload and 
                self._config_cache is not None and 
                self._last_modified == current_modified):
                return self._config_cache
                
            # Load configuration from file
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Validate configuration
            config = self.validate_config(config)
            
            # Update cache
            self._config_cache = config
            self._last_modified = current_modified
            
            self.logger.info(f"Configuration loaded from {self.config_file}")
            return config
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            raise ConfigurationError(f"Invalid JSON configuration: {e}")
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise ConfigurationError(f"Configuration load error: {e}")
            
    def validate_config(self, config: Dict) -> Dict:
        """Validate and merge configuration with defaults"""
        try:
            # Ensure required sections exist
            required_sections = ['strategy_settings', 'technical_analysis']
            for section in required_sections:
                if section not in config:
                    self.logger.warning(f"Missing section '{section}', using defaults")
                    config[section] = self.defaults.get(section, {})
                    
            # Validate strategy settings
            strategy = config['strategy_settings']
            if 'symbols' not in strategy or not strategy['symbols']:
                raise ConfigurationError("No symbols specified in configuration")
                
            # Validate timeframe
            valid_timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
            if strategy.get('timeframe', 'M1') not in valid_timeframes:
                self.logger.warning(f"Invalid timeframe, using M1")
                strategy['timeframe'] = 'M1'
                
            # Validate confidence threshold
            threshold = strategy.get('min_confidence_threshold', 0.7)
            if not 0.0 <= threshold <= 1.0:
                self.logger.warning(f"Invalid confidence threshold {threshold}, using 0.7")
                strategy['min_confidence_threshold'] = 0.7
                
            return config
            
        except Exception as e:
            self.logger.error(f"Configuration validation error: {e}")
            raise ConfigurationError(f"Configuration validation failed: {e}")
            
    def get_strategy_config(self) -> StrategyConfig:
        """Convert loaded configuration to StrategyConfig object"""
        config = self.load_config()
        settings = config['strategy_settings']
        
        return StrategyConfig(
            strategy_name=settings.get('strategy_name', 'ConfigurableStrategy'),
            strategy_version=settings.get('strategy_version', '1.0'),
            symbols=settings.get('symbols', ['BTCUSD']),
            timeframe=settings.get('timeframe', 'M1'),
            max_concurrent_positions=settings.get('max_concurrent_positions', 3),
            signal_cooldown_minutes=settings.get('signal_cooldown_minutes', 5),
            min_confidence_threshold=settings.get('min_confidence_threshold', 0.7),
            enabled=settings.get('enabled', True),
            risk_parameters=config.get('risk_management', {}),
            custom_parameters={
                'technical_analysis': config.get('technical_analysis', {}),
                'execution': config.get('execution', {}),
                'performance_tracking': config.get('performance_tracking', {}),
                'symbol_specific': config.get('symbol_specific', {}),
                'alerts': config.get('alerts', {}),
                'development': config.get('development', {})
            }
        )
        
    def get_technical_config(self, symbol: str = None) -> TechnicalConfig:
        """Get technical analysis configuration for a specific symbol or generic defaults"""
        config = self.load_config()
        
        # If symbol specified, try to get symbol-specific configuration first
        if symbol:
            symbol_specific = config.get('symbol_specific', {})
            symbol_config = symbol_specific.get(symbol, {})
            symbol_ta = symbol_config.get('technical_analysis', {})
            
            if symbol_ta:  # Use symbol-specific configuration
                return TechnicalConfig(
                    sma_fast=symbol_ta.get('sma_fast', 20),
                    sma_slow=symbol_ta.get('sma_slow', 50),
                    ema_fast=symbol_ta.get('ema_fast', 12),
                    ema_slow=symbol_ta.get('ema_slow', 26),
                    macd_fast=symbol_ta.get('macd_fast', 12),
                    macd_slow=symbol_ta.get('macd_slow', 26),
                    macd_signal=symbol_ta.get('macd_signal', 9),
                    rsi_period=symbol_ta.get('rsi_period', 14),
                    rsi_overbought=symbol_ta.get('rsi_overbought', 70.0),
                    rsi_oversold=symbol_ta.get('rsi_oversold', 30.0),
                    bb_period=symbol_ta.get('bb_period', 20),
                    bb_std_dev=symbol_ta.get('bb_std_dev', 2.0),
                    atr_period=symbol_ta.get('atr_period', 14),
                    adx_period=symbol_ta.get('adx_period', 14),
                    adx_strong_trend=symbol_ta.get('adx_strong_trend', 25.0),
                    adx_very_strong_trend=symbol_ta.get('adx_very_strong_trend', 40.0),
                    volume_sma_period=symbol_ta.get('volume_sma_period', 20),
                    volume_spike_multiplier=symbol_ta.get('volume_spike_multiplier', 2.0)
                )
        
        # Fallback to generic configuration from technical_analysis section
        ta_config = config.get('technical_analysis', {})
        indicators = ta_config.get('indicators', {})
        
        # Moving averages
        ma = indicators.get('moving_averages', {})
        
        # MACD
        macd = indicators.get('macd', {})
        
        # RSI 
        rsi = indicators.get('rsi', {})
        
        # Bollinger Bands
        bb = indicators.get('bollinger_bands', {})
        
        # ATR
        atr = indicators.get('atr', {})
        
        # ADX
        adx = indicators.get('adx', {})
        
        # Volume
        volume = indicators.get('volume', {})
        
        return TechnicalConfig(
            sma_fast=ma.get('sma_fast', 20),
            sma_slow=ma.get('sma_slow', 50),
            ema_fast=ma.get('ema_fast', 12),
            ema_slow=ma.get('ema_slow', 26),
            macd_fast=macd.get('fast_period', 12),
            macd_slow=macd.get('slow_period', 26),
            macd_signal=macd.get('signal_period', 9),
            rsi_period=rsi.get('period', 14),
            rsi_overbought=rsi.get('overbought_level', 70.0),
            rsi_oversold=rsi.get('oversold_level', 30.0),
            bb_period=bb.get('period', 20),
            bb_std_dev=bb.get('std_dev_multiplier', 2.0),
            atr_period=atr.get('period', 14),
            adx_period=adx.get('period', 14),
            adx_strong_trend=adx.get('strong_trend', 25.0),
            adx_very_strong_trend=adx.get('very_strong_trend', 40.0),
            volume_sma_period=volume.get('sma_period', 20),
            volume_spike_multiplier=volume.get('volume_spike_multiplier', 2.0)
        )
        
    def get_signal_config(self) -> SignalConfig:
        """Get signal generation configuration"""
        config = self.load_config()
        signals = config.get('technical_analysis', {}).get('signal_conditions', {})
        
        bullish = signals.get('bullish', {})
        bearish = signals.get('bearish', {})
        confidence = signals.get('confidence_calculation', {})
        
        return SignalConfig(
            bullish_sma_crossover=bullish.get('sma_crossover', True),
            bullish_price_above_sma=bullish.get('price_above_sma_fast', True),
            bullish_min_separation=bullish.get('min_separation_percent', 0.1),
            bullish_rsi_min=bullish.get('rsi_min', 40.0),
            bullish_rsi_max=bullish.get('rsi_max', 80.0),
            bearish_sma_crossover=bearish.get('sma_crossover', True),
            bearish_price_below_sma=bearish.get('price_below_sma_fast', True),
            bearish_min_separation=bearish.get('min_separation_percent', 0.1),
            bearish_rsi_min=bearish.get('rsi_min', 20.0),
            bearish_rsi_max=bearish.get('rsi_max', 60.0),
            base_confidence=confidence.get('base_confidence', 0.6),
            separation_multiplier=confidence.get('separation_multiplier', 10.0),
            max_confidence=confidence.get('max_confidence', 0.95),
            rsi_weight=confidence.get('rsi_weight', 0.1),
            volume_weight=confidence.get('volume_weight', 0.05)
        )
        
    def get_risk_config(self) -> RiskConfig:
        """Get risk management configuration"""
        config = self.load_config()
        risk = config.get('risk_management', {})
        
        positioning = risk.get('position_sizing', {})
        exposure = risk.get('exposure_limits', {})
        market_cond = risk.get('market_conditions', {})
        
        return RiskConfig(
            use_smart_filtering=positioning.get('use_smart_filtering', True),
            max_position_percent=positioning.get('max_position_percent_account', 15.0),
            btc_max_coefficient=positioning.get('btc_max_coefficient', 1.0),
            min_safe_coefficient=positioning.get('min_safe_coefficient', 1.0),
            max_total_exposure_percent=exposure.get('max_total_exposure_percent', 25.0),
            max_daily_loss_percent=exposure.get('max_daily_loss_percent', 5.0),
            max_drawdown_percent=exposure.get('max_drawdown_percent', 15.0),
            min_account_balance=exposure.get('min_account_balance', 1000.0),
            normal_multiplier=market_cond.get('normal_multiplier', 1.0),
            bull_multiplier=market_cond.get('bull_market_multiplier', 1.2),
            bear_multiplier=market_cond.get('bear_market_multiplier', 0.5),
            high_vol_multiplier=market_cond.get('high_volatility_multiplier', 0.7),
            low_vol_multiplier=market_cond.get('low_volatility_multiplier', 1.3),
            news_multiplier=market_cond.get('news_event_multiplier', 0.3),
            emergency_multiplier=market_cond.get('emergency_multiplier', 0.1)
        )
        
    def get_execution_config(self) -> ExecutionConfig:
        """Get execution configuration"""
        config = self.load_config()
        execution = config.get('execution', {})
        
        orders = execution.get('order_settings', {})
        threading = execution.get('threading', {})
        data_mgmt = execution.get('data_management', {})
        
        return ExecutionConfig(
            deviation_points=orders.get('deviation_points', 20),
            order_timeout=orders.get('order_timeout_seconds', 30),
            max_slippage_percent=orders.get('max_slippage_percent', 0.1),
            filling_type=orders.get('order_filling_type', 'IOC'),
            max_workers=threading.get('max_workers_per_symbol', 1),
            analysis_timeout=threading.get('analysis_timeout_per_symbol', 30),
            concurrent_analysis=threading.get('concurrent_analysis', True),
            historical_bars=data_mgmt.get('historical_bars', 1000),
            min_bars_analysis=data_mgmt.get('min_bars_for_analysis', 50),
            cache_refresh_minutes=data_mgmt.get('cache_refresh_minutes', 1),
            data_validation=data_mgmt.get('data_validation', True)
        )
        
    def get_symbol_specific_config(self, symbol: str) -> Dict:
        """Get symbol-specific configuration"""
        config = self.load_config()
        symbol_specific = config.get('symbol_specific', {})
        return symbol_specific.get(symbol, {})
        
    def update_config(self, section: str, key: str, value: Any) -> bool:
        """Update a configuration value and save to file"""
        try:
            config = self.load_config(force_reload=True)
            
            # Navigate to the section and update the value
            if section not in config:
                config[section] = {}
                
            config[section][key] = value
            config['last_updated'] = datetime.now().isoformat()
            
            # Save updated configuration
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            # Clear cache to force reload
            self._config_cache = None
            
            self.logger.info(f"Updated {section}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {e}")
            return False
            
    def save_current_config_as_template(self, template_name: str) -> bool:
        """Save current configuration as a template for future use"""
        try:
            config = self.load_config()
            template_file = f"{template_name}_config_template.json"
            
            with open(template_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"Configuration template saved as {template_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving template: {e}")
            return False


def main():
    """Demonstration of configuration loader"""
    print("🔧 Strategy Configuration Loader - Demo")
    print("=" * 50)
    
    # Initialize config loader
    config_loader = ConfigurationLoader()
    
    # Test loading configuration
    print("\n📋 Loading Configuration...")
    try:
        # Get strategy configuration
        strategy_config = config_loader.get_strategy_config()
        print(f"Strategy: {strategy_config.strategy_name} v{strategy_config.strategy_version}")
        print(f"Symbols: {', '.join(strategy_config.symbols)}")
        print(f"Timeframe: {strategy_config.timeframe}")
        print(f"Min Confidence: {strategy_config.min_confidence_threshold:.1%}")
        print(f"Max Positions: {strategy_config.max_concurrent_positions}")
        
        # Get symbol-specific technical analysis configuration
        print("\n📊 Symbol-Specific Technical Analysis Configuration:")
        symbols_to_show = strategy_config.symbols[:3]  # Show first 3 symbols
        
        for symbol in symbols_to_show:
            tc = config_loader.get_technical_config(symbol)
            print(f"\n{symbol}:")
            print(f"  SMA: {tc.sma_fast}/{tc.sma_slow}, EMA: {tc.ema_fast}/{tc.ema_slow}")
            print(f"  MACD: {tc.macd_fast}/{tc.macd_slow}/{tc.macd_signal}")
            print(f"  RSI: {tc.rsi_period} (OB:{tc.rsi_overbought}, OS:{tc.rsi_oversold})")
            print(f"  ADX: {tc.adx_period} (Strong:{tc.adx_strong_trend}, VStrong:{tc.adx_very_strong_trend})")
            print(f"  BB: {tc.bb_period}/{tc.bb_std_dev}, ATR: {tc.atr_period}, Vol: {tc.volume_sma_period}")
        
        # Get signal configuration
        print("\n🎯 Signal Configuration:")
        signal_config = config_loader.get_signal_config()
        print(f"Base Confidence: {signal_config.base_confidence:.2f}")
        print(f"Max Confidence: {signal_config.max_confidence:.2f}")
        print(f"Bullish RSI Range: {signal_config.bullish_rsi_min}-{signal_config.bullish_rsi_max}")
        print(f"Bearish RSI Range: {signal_config.bearish_rsi_min}-{signal_config.bearish_rsi_max}")
        
        # Get risk configuration
        print("\n🛡️ Risk Management Configuration:")
        risk_config = config_loader.get_risk_config()
        print(f"Max Position %: {risk_config.max_position_percent}%")
        print(f"Max Total Exposure: {risk_config.max_total_exposure_percent}%")
        print(f"BTC Max Coefficient: {risk_config.btc_max_coefficient}")
        print(f"Emergency Multiplier: {risk_config.emergency_multiplier}")
        
        # Get execution configuration
        print("\n⚡ Execution Configuration:")
        exec_config = config_loader.get_execution_config()
        print(f"Deviation Points: {exec_config.deviation_points}")
        print(f"Historical Bars: {exec_config.historical_bars}")
        print(f"Concurrent Analysis: {exec_config.concurrent_analysis}")
        
        # Test symbol-specific configuration
        print("\n🔍 Symbol-Specific Configuration:")
        btc_config = config_loader.get_symbol_specific_config("BTCUSD")
        if btc_config:
            print(f"BTCUSD - Min Confidence Override: {btc_config.get('min_confidence_override', 'None')}")
            print(f"BTCUSD - High Volatility Filter: {btc_config.get('special_conditions', {}).get('high_volatility_filter', 'None')}")
        
        # Test configuration update
        print("\n🔄 Testing Configuration Update...")
        if config_loader.update_config('strategy_settings', 'min_confidence_threshold', 0.8):
            print("✅ Configuration updated successfully")
            updated_config = config_loader.get_strategy_config()
            print(f"New Min Confidence: {updated_config.min_confidence_threshold:.1%}")
        
        print("\n✅ Configuration loader demo completed successfully!")
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    main()
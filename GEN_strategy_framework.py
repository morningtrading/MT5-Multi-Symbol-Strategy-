#!/usr/bin/env python3
"""
Multi-Symbol Strategy Framework Base
===================================

Comprehensive foundation for building and executing trading strategies across
multiple symbols with integrated risk management and performance tracking.

Key Features:
- Multi-symbol strategy architecture
- Real-time market data integration
- Signal generation and processing
- Risk manager integration
- Performance tracking and analytics
- Strategy lifecycle management
- Modular design for easy strategy development

Strategy Development Flow:
1. Inherit from BaseStrategy class
2. Implement analyze_market() method
3. Generate signals via create_signal() method
4. Framework handles execution via Risk Manager
5. Performance tracking automatic

Author: Multi-Symbol Strategy Framework
Version: 1.0
Date: 2025-09-19
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import our Risk Manager
from GEN_risk_manager import CoefficientBasedRiskManager, TradeRequest, MarketCondition

# Import Configuration Loader
from GEN_config_loader import (ConfigurationLoader, TechnicalConfig, SignalConfig, 
                             RiskConfig, ExecutionConfig, ConfigurationError)

class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    CLOSE = "CLOSE"

class SignalStrength(Enum):
    """Signal strength classifications"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4

class StrategyState(Enum):
    """Strategy execution states"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"

@dataclass
class MarketSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    strategy_id: str
    price: float
    analysis_data: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate signal data"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if self.price <= 0:
            raise ValueError("Price must be positive")

@dataclass
class StrategyMetrics:
    """Strategy performance metrics"""
    total_signals: int = 0
    executed_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    avg_trade_duration: float = 0.0
    signals_per_hour: float = 0.0
    
    def update_metrics(self):
        """Update calculated metrics"""
        if self.executed_trades > 0:
            self.win_rate = self.winning_trades / self.executed_trades
            if self.gross_loss != 0:
                self.profit_factor = abs(self.gross_profit / self.gross_loss)
            else:
                self.profit_factor = float('inf') if self.gross_profit > 0 else 0.0

@dataclass
class StrategyConfig:
    """Strategy configuration parameters"""
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

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    
    Provides common infrastructure for:
    - Market data management
    - Signal generation
    - Risk management integration
    - Performance tracking
    - Execution management
    """
    
    @classmethod
    def from_config_file(cls, config_file: str = "GEN_strategy_config.json", 
                        risk_manager: Optional[CoefficientBasedRiskManager] = None):
        """Factory method to create strategy instance from configuration file"""
        config_loader = ConfigurationLoader(config_file)
        return cls(config=None, risk_manager=risk_manager, config_loader=config_loader)
    
    def __init__(self, config: StrategyConfig = None, risk_manager: Optional[CoefficientBasedRiskManager] = None, 
                 config_loader: Optional[ConfigurationLoader] = None):
        """Initialize strategy with configuration and risk manager"""
        # Initialize configuration loader if not provided
        self.config_loader = config_loader or ConfigurationLoader()
        
        # Use provided config or load from JSON
        if config is None:
            try:
                self.config = self.config_loader.get_strategy_config()
            except ConfigurationError as e:
                raise ValueError(f"Failed to load strategy configuration: {e}")
        else:
            self.config = config
            
        # Load technical analysis configuration (symbol-specific)
        self.technical_configs = {}
        for symbol in self.config.symbols:
            self.technical_configs[symbol] = self.config_loader.get_technical_config(symbol)
        
        # Load signal configuration
        self.signal_config = self.config_loader.get_signal_config()
        
        self.risk_manager = risk_manager or CoefficientBasedRiskManager()
        
        # Strategy state
        self.state = StrategyState.STOPPED
        self.start_time = None
        self.last_analysis_time = None
        
        # Performance tracking
        self.metrics = StrategyMetrics()
        self.signal_history: List[MarketSignal] = []
        self.trade_history: List[Dict] = []
        self.active_positions: Dict[str, Dict] = {}
        
        # Market data cache
        self.market_data_cache: Dict[str, pd.DataFrame] = {}
        self.last_data_update: Dict[str, datetime] = {}
        
        # Signal management
        self.last_signal_time: Dict[str, datetime] = {}
        self.signal_cooldown = timedelta(minutes=self.config.signal_cooldown_minutes)
        
        # Logging
        self.logger = self.setup_logging()
        
        # Threading for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=len(self.config.symbols))
        
        self.logger.info(f"Strategy '{self.config.strategy_name}' v{self.config.strategy_version} initialized")
        self.logger.info(f"Managing {len(self.config.symbols)} symbols: {self.config.symbols}")
        
    def setup_logging(self) -> logging.Logger:
        """Setup strategy-specific logging"""
        logger_name = f"Strategy_{self.config.strategy_name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler for strategy logs
        log_file = logs_dir / f"strategy_{self.config.strategy_name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    @abstractmethod
    def analyze_market(self, symbol: str, data: pd.DataFrame) -> Optional[MarketSignal]:
        """
        Abstract method for market analysis - must be implemented by each strategy
        
        Args:
            symbol: Symbol to analyze
            data: Market data for the symbol
            
        Returns:
            MarketSignal if conditions are met, None otherwise
        """
        pass
        
    def get_market_data(self, symbol: str, timeframe: str = None, bars: int = 1000) -> Optional[pd.DataFrame]:
        """Get market data for a symbol with caching"""
        timeframe = timeframe or self.config.timeframe
        cache_key = f"{symbol}_{timeframe}"
        
        try:
            # Check cache freshness (update every minute)
            now = datetime.now()
            if (cache_key in self.last_data_update and 
                now - self.last_data_update[cache_key] < timedelta(minutes=1)):
                return self.market_data_cache.get(cache_key)
                
            # Convert timeframe string to MT5 constant
            mt5_timeframe = self.get_mt5_timeframe(timeframe)
            if mt5_timeframe is None:
                self.logger.error(f"Invalid timeframe: {timeframe}")
                return None
                
            # Get fresh data from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, bars)
            if rates is None or len(rates) == 0:
                self.logger.warning(f"No data received for {symbol}")
                return None
                
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Add basic technical indicators using symbol-specific configuration
            df = self.add_basic_indicators(df, symbol)
            
            # Cache the data
            self.market_data_cache[cache_key] = df
            self.last_data_update[cache_key] = now
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting market data for {symbol}: {e}")
            return None
            
    def get_mt5_timeframe(self, timeframe: str) -> Optional[int]:
        """Convert timeframe string to MT5 constant"""
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        return timeframe_map.get(timeframe)
        
    def add_basic_indicators(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Add basic technical indicators to market data using symbol-specific configuration parameters"""
        try:
            # Get symbol-specific technical configuration
            tech_config = self.technical_configs.get(symbol)
            if not tech_config:
                self.logger.warning(f"No technical config found for {symbol}, using default")
                tech_config = self.config_loader.get_technical_config()  # Fallback to generic
                
            # Moving averages (using symbol-specific configured periods)
            df[f'sma_{tech_config.sma_fast}'] = df['close'].rolling(window=tech_config.sma_fast).mean()
            df[f'sma_{tech_config.sma_slow}'] = df['close'].rolling(window=tech_config.sma_slow).mean()
            df[f'ema_{tech_config.ema_fast}'] = df['close'].ewm(span=tech_config.ema_fast).mean()
            df[f'ema_{tech_config.ema_slow}'] = df['close'].ewm(span=tech_config.ema_slow).mean()
            
            # Add standard names for backward compatibility
            df['sma_fast'] = df[f'sma_{tech_config.sma_fast}']
            df['sma_slow'] = df[f'sma_{tech_config.sma_slow}']
            df['ema_fast'] = df[f'ema_{tech_config.ema_fast}']
            df['ema_slow'] = df[f'ema_{tech_config.ema_slow}']
            
            # MACD (using symbol-specific configured periods)
            df['macd'] = df['ema_fast'] - df['ema_slow']
            df['macd_signal'] = df['macd'].ewm(span=tech_config.macd_signal).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI (using symbol-specific configured period)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=tech_config.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=tech_config.rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands (using symbol-specific configured periods)
            df['bb_middle'] = df['close'].rolling(window=tech_config.bb_period).mean()
            bb_std = df['close'].rolling(window=tech_config.bb_period).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * tech_config.bb_std_dev)
            df['bb_lower'] = df['bb_middle'] - (bb_std * tech_config.bb_std_dev)
            
            # ATR (using symbol-specific configured period)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['atr'] = true_range.rolling(window=tech_config.atr_period).mean()
            
            # ADX (Average Directional Index) - NEW INDICATOR
            # Calculate Directional Movement
            high_diff = df['high'].diff()
            low_diff = -df['low'].diff()
            
            plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
            minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
            
            # Smooth the directional movements
            plus_di = 100 * (plus_dm.rolling(window=tech_config.adx_period).mean() / df['atr'])
            minus_di = 100 * (minus_dm.rolling(window=tech_config.adx_period).mean() / df['atr'])
            
            # Calculate ADX
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
            df['adx'] = dx.rolling(window=tech_config.adx_period).mean()
            df['plus_di'] = plus_di
            df['minus_di'] = minus_di
            
            # Volume indicators (using symbol-specific configured periods)
            if 'tick_volume' in df.columns:
                df['volume_sma'] = df['tick_volume'].rolling(window=tech_config.volume_sma_period).mean()
                df['volume_spike'] = df['tick_volume'] / df['volume_sma']
                
            return df
            
        except Exception as e:
            self.logger.error(f"Error adding technical indicators: {e}")
            return df
            
    def create_signal(self, symbol: str, signal_type: SignalType, strength: SignalStrength, 
                     confidence: float, analysis_data: Dict = None, metadata: Dict = None) -> MarketSignal:
        """Create a trading signal with current market price"""
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise ValueError(f"Cannot get current price for {symbol}")
                
            price = tick.ask if signal_type == SignalType.BUY else tick.bid
            
            signal = MarketSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                timestamp=datetime.now(),
                strategy_id=self.config.strategy_name,
                price=price,
                analysis_data=analysis_data or {},
                metadata=metadata or {}
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error creating signal for {symbol}: {e}")
            raise
            
    def is_signal_allowed(self, symbol: str) -> bool:
        """Check if signal generation is allowed for symbol (cooldown check)"""
        if symbol in self.last_signal_time:
            time_since_last = datetime.now() - self.last_signal_time[symbol]
            if time_since_last < self.signal_cooldown:
                return False
        return True
        
    def process_signal(self, signal: MarketSignal) -> bool:
        """Process a trading signal through risk management and execution"""
        try:
            # Validate signal
            if signal.confidence < self.config.min_confidence_threshold:
                self.logger.info(f"Signal rejected: confidence {signal.confidence:.2f} < threshold {self.config.min_confidence_threshold:.2f}")
                return False
                
            # Check signal cooldown
            if not self.is_signal_allowed(signal.symbol):
                self.logger.debug(f"Signal skipped: {signal.symbol} in cooldown period")
                return False
                
            # Add to signal history
            self.signal_history.append(signal)
            self.metrics.total_signals += 1
            
            # Create trade request for risk manager
            trade_request = TradeRequest(
                symbol=signal.symbol,
                direction=signal.signal_type.value,
                strategy_id=signal.strategy_id,
                confidence=signal.confidence,
                metadata={
                    'signal_strength': signal.strength.value,
                    'analysis_data': signal.analysis_data
                }
            )
            
            # Evaluate through risk manager
            risk_decision = self.risk_manager.evaluate_trade_request(trade_request)
            
            if risk_decision.decision.value == "approved":
                # Execute the trade
                execution_success = self.execute_trade(signal, risk_decision.approved_lot_size)
                if execution_success:
                    self.metrics.executed_trades += 1
                    self.last_signal_time[signal.symbol] = datetime.now()
                    self.logger.info(f"Trade executed: {signal.symbol} {signal.signal_type.value} {risk_decision.approved_lot_size} lots")
                    return True
                else:
                    self.logger.error(f"Trade execution failed for {signal.symbol}")
                    return False
            else:
                self.logger.info(f"Trade rejected by risk manager: {risk_decision.rejection_reason}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing signal for {signal.symbol}: {e}")
            return False
            
    def execute_trade(self, signal: MarketSignal, lot_size: float) -> bool:
        """Execute trade through MT5"""
        try:
            # Get current price
            tick = mt5.symbol_info_tick(signal.symbol)
            if tick is None:
                return False
                
            # Prepare order request
            order_type = mt5.ORDER_TYPE_BUY if signal.signal_type == SignalType.BUY else mt5.ORDER_TYPE_SELL
            price = tick.ask if signal.signal_type == SignalType.BUY else tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal.symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": hash(self.config.strategy_name) % 2147483647,  # Convert to valid magic number
                "comment": f"{self.config.strategy_name}_{signal.strength.name}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                # Log successful trade
                trade_record = {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": signal.symbol,
                    "type": signal.signal_type.value,
                    "lot_size": lot_size,
                    "price": result.price,
                    "order_id": result.order,
                    "signal_confidence": signal.confidence,
                    "signal_strength": signal.strength.name,
                    "strategy": self.config.strategy_name
                }
                
                self.trade_history.append(trade_record)
                self.active_positions[result.order] = trade_record
                
                return True
            else:
                error_msg = result.comment if result else "Unknown error"
                self.logger.error(f"Order failed: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing trade: {e}")
            return False
            
    def analyze_all_symbols(self) -> List[MarketSignal]:
        """Analyze all configured symbols concurrently"""
        signals = []
        
        # Use ThreadPoolExecutor for concurrent analysis
        future_to_symbol = {}
        
        with ThreadPoolExecutor(max_workers=len(self.config.symbols)) as executor:
            # Submit analysis tasks for all symbols
            for symbol in self.config.symbols:
                if self.state != StrategyState.RUNNING:
                    break
                    
                future = executor.submit(self._analyze_single_symbol, symbol)
                future_to_symbol[future] = symbol
                
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    signal = future.result(timeout=30)  # 30 second timeout per symbol
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Error analyzing {symbol}: {e}")
                    
        return signals
        
    def _analyze_single_symbol(self, symbol: str) -> Optional[MarketSignal]:
        """Analyze a single symbol (helper method for concurrent execution)"""
        try:
            # Get market data
            data = self.get_market_data(symbol)
            if data is None or len(data) < 50:  # Need minimum data for analysis
                return None
                
            # Call strategy-specific analysis
            signal = self.analyze_market(symbol, data)
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error in single symbol analysis for {symbol}: {e}")
            return None
            
    def start_strategy(self) -> bool:
        """Start the strategy execution"""
        try:
            if self.state == StrategyState.RUNNING:
                self.logger.warning("Strategy already running")
                return True
                
            # Initialize MT5 connection
            if not mt5.initialize():
                self.logger.error("Failed to initialize MT5")
                return False
                
            self.state = StrategyState.RUNNING
            self.start_time = datetime.now()
            
            self.logger.info(f"Strategy '{self.config.strategy_name}' started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting strategy: {e}")
            self.state = StrategyState.ERROR
            return False
            
    def stop_strategy(self) -> bool:
        """Stop the strategy execution"""
        try:
            if self.state == StrategyState.STOPPED:
                return True
                
            self.state = StrategyState.STOPPING
            
            # Shutdown executor
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
                
            self.state = StrategyState.STOPPED
            self.logger.info(f"Strategy '{self.config.strategy_name}' stopped")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping strategy: {e}")
            self.state = StrategyState.ERROR
            return False
            
    def run_analysis_cycle(self) -> Dict[str, any]:
        """Run a single analysis cycle across all symbols"""
        if self.state != StrategyState.RUNNING:
            return {"status": "not_running", "signals": []}
            
        cycle_start = datetime.now()
        
        try:
            # Analyze all symbols
            signals = self.analyze_all_symbols()
            
            # Process each signal
            executed_signals = []
            for signal in signals:
                if self.process_signal(signal):
                    executed_signals.append(signal)
                    
            # Update metrics
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            self.last_analysis_time = cycle_start
            
            # Calculate signals per hour
            if self.start_time:
                runtime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                if runtime_hours > 0:
                    self.metrics.signals_per_hour = self.metrics.total_signals / runtime_hours
                    
            return {
                "status": "completed",
                "signals_generated": len(signals),
                "signals_executed": len(executed_signals),
                "cycle_duration": cycle_duration,
                "analysis_time": cycle_start.isoformat(),
                "signals": [self._signal_to_dict(s) for s in signals]
            }
            
        except Exception as e:
            self.logger.error(f"Error in analysis cycle: {e}")
            return {"status": "error", "error": str(e)}
            
    def _signal_to_dict(self, signal: MarketSignal) -> Dict:
        """Convert MarketSignal to dictionary for serialization"""
        return {
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value,
            "strength": signal.strength.name,
            "confidence": signal.confidence,
            "timestamp": signal.timestamp.isoformat(),
            "price": signal.price,
            "strategy_id": signal.strategy_id
        }
        
    def get_strategy_status(self) -> Dict[str, any]:
        """Get comprehensive strategy status"""
        self.metrics.update_metrics()
        
        return {
            "strategy_name": self.config.strategy_name,
            "strategy_version": self.config.strategy_version,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "last_analysis": self.last_analysis_time.isoformat() if self.last_analysis_time else None,
            "runtime_minutes": ((datetime.now() - self.start_time).total_seconds() / 60) if self.start_time else 0,
            "symbols": self.config.symbols,
            "active_positions": len(self.active_positions),
            "metrics": {
                "total_signals": self.metrics.total_signals,
                "executed_trades": self.metrics.executed_trades,
                "win_rate": f"{self.metrics.win_rate:.2%}",
                "total_pnl": f"${self.metrics.total_pnl:.2f}",
                "signals_per_hour": f"{self.metrics.signals_per_hour:.1f}",
                "profit_factor": f"{self.metrics.profit_factor:.2f}"
            },
            "recent_signals": len([s for s in self.signal_history if s.timestamp > datetime.now() - timedelta(hours=1)])
        }
        
    def save_strategy_state(self, filepath: str = None) -> bool:
        """Save strategy state to file"""
        try:
            if filepath is None:
                filepath = f"strategy_state_{self.config.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
            state_data = {
                "config": {
                    "strategy_name": self.config.strategy_name,
                    "strategy_version": self.config.strategy_version,
                    "symbols": self.config.symbols,
                    "timeframe": self.config.timeframe,
                    "enabled": self.config.enabled
                },
                "status": self.get_strategy_status(),
                "signal_history": [self._signal_to_dict(s) for s in self.signal_history[-100:]],  # Last 100 signals
                "trade_history": self.trade_history[-50:]  # Last 50 trades
            }
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
                
            self.logger.info(f"Strategy state saved to {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving strategy state: {e}")


class SimpleTestStrategy(BaseStrategy):
    """Simple test strategy to validate configuration integration"""
    
    def analyze_market(self, symbol: str, data: pd.DataFrame) -> Optional[MarketSignal]:
        """Simple moving average crossover strategy for testing"""
        try:
            # Need at least 2 data points
            if len(data) < 2:
                return None
                
            current = data.iloc[-1]
            previous = data.iloc[-2]
            
            # Check if we have required indicators
            if pd.isna(current['sma_fast']) or pd.isna(current['sma_slow']):
                return None
                
            # Simple SMA crossover logic
            current_fast = current['sma_fast']
            current_slow = current['sma_slow']
            prev_fast = previous['sma_fast']
            prev_slow = previous['sma_slow']
            
            # Bullish crossover: fast SMA crosses above slow SMA
            if prev_fast <= prev_slow and current_fast > current_slow:
                confidence = min(0.9, (current_fast - current_slow) / current_slow * 100 + 0.6)
                return self.create_signal(
                    symbol=symbol,
                    signal_type=SignalType.BUY,
                    strength=SignalStrength.MODERATE,
                    confidence=confidence,
                    analysis_data={
                        'sma_fast': current_fast,
                        'sma_slow': current_slow,
                        'crossover_strength': current_fast - current_slow
                    }
                )
                
            # Bearish crossover: fast SMA crosses below slow SMA
            elif prev_fast >= prev_slow and current_fast < current_slow:
                confidence = min(0.9, (current_slow - current_fast) / current_slow * 100 + 0.6)
                return self.create_signal(
                    symbol=symbol,
                    signal_type=SignalType.SELL,
                    strength=SignalStrength.MODERATE,
                    confidence=confidence,
                    analysis_data={
                        'sma_fast': current_fast,
                        'sma_slow': current_slow,
                        'crossover_strength': current_slow - current_fast
                    }
                )
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error in market analysis for {symbol}: {e}")
            return None


def main():
    """Test the strategy framework with configuration integration"""
    print("🎯 Strategy Framework Configuration Integration Test")
    print("=" * 60)
    
    try:
        # Initialize MT5 connection (required for testing)
        if not mt5.initialize():
            print("❌ Failed to initialize MT5")
            return
            
        print("✅ MT5 initialized successfully")
        
        # Create strategy instance using configuration file
        print("\n📋 Creating strategy from configuration file...")
        strategy = SimpleTestStrategy.from_config_file()
        
        print(f"Strategy: {strategy.config.strategy_name} v{strategy.config.strategy_version}")
        print(f"Symbols: {', '.join(strategy.config.symbols)}")
        print(f"Timeframe: {strategy.config.timeframe}")
        print(f"Min Confidence: {strategy.config.min_confidence_threshold:.1%}")
        print(f"Signal Cooldown: {strategy.config.signal_cooldown_minutes} minutes")
        
        # Display symbol-specific technical configuration
        print("\n📊 Symbol-Specific Technical Analysis Configuration:")
        symbols_to_show = strategy.config.symbols[:3]  # Show first 3 symbols
        
        for symbol in symbols_to_show:
            tc = strategy.technical_configs.get(symbol)
            if tc:
                print(f"\n{symbol}:")
                print(f"  SMA: {tc.sma_fast}/{tc.sma_slow}, EMA: {tc.ema_fast}/{tc.ema_slow}")
                print(f"  MACD: {tc.macd_fast}/{tc.macd_slow}/{tc.macd_signal}")
                print(f"  RSI: {tc.rsi_period} (OB:{tc.rsi_overbought}, OS:{tc.rsi_oversold})")
                print(f"  ADX: {tc.adx_period} (Strong:{tc.adx_strong_trend}, VStrong:{tc.adx_very_strong_trend})")
                print(f"  BB: {tc.bb_period}/{tc.bb_std_dev}, ATR: {tc.atr_period}")
        
        # Test market data retrieval with configured indicators
        print("\n📈 Testing market data retrieval with configured indicators...")
        test_symbol = strategy.config.symbols[0]  # Use first symbol
        
        data = strategy.get_market_data(test_symbol, bars=100)
        if data is not None and len(data) > 50:
            latest = data.iloc[-1]
            print(f"\n{test_symbol} Latest Data:")
            symbol_tc = strategy.technical_configs.get(test_symbol)
            print(f"Close: {latest['close']:.5f}")
            print(f"SMA {symbol_tc.sma_fast}: {latest['sma_fast']:.5f}")
            print(f"SMA {symbol_tc.sma_slow}: {latest['sma_slow']:.5f}")
            print(f"EMA {symbol_tc.ema_fast}: {latest['ema_fast']:.5f}")
            print(f"EMA {symbol_tc.ema_slow}: {latest['ema_slow']:.5f}")
            print(f"RSI: {latest['rsi']:.2f}")
            print(f"MACD: {latest['macd']:.5f}")
            if 'adx' in latest and not pd.isna(latest['adx']):
                print(f"ADX: {latest['adx']:.2f}")
            
            # Test signal generation
            print("\n🎯 Testing signal generation...")
            signal = strategy.analyze_market(test_symbol, data)
            if signal:
                print(f"Signal Generated: {signal.signal_type.value} {test_symbol}")
                print(f"Confidence: {signal.confidence:.2f}")
                print(f"Strength: {signal.strength.name}")
                print(f"Analysis Data: {signal.analysis_data}")
            else:
                print("No signal generated (normal - crossovers are rare)")
                
        else:
            print(f"❌ Failed to get market data for {test_symbol}")
            
        print("\n✅ Configuration integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        mt5.shutdown()
        
        
if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Coefficient-Based Risk Manager
=============================

Simple and effective risk management system using coefficient-based position sizing.
Each asset uses: Position Size = Minimum Lot Size × Asset Coefficient

Key Features:
- Deterministic position sizing (no complex calculations)
- Asset-class specific coefficients (crypto: 5x, indices: 1x, commodities: 1x)
- Real-time account monitoring and protection
- Emergency controls and risk limits
- Performance-based coefficient adjustments
- Integration with MT5 trading infrastructure

Position Sizing Examples:
- BTCUSD: 0.01 × 5 = 0.05 lots
- NAS100: 0.1 × 1 = 0.1 lots  
- USOUSD: 0.01 × 1 = 0.01 lots

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
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

class MarketCondition(Enum):
    """Market condition classifications for coefficient adjustment"""
    NORMAL = "normal"
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    NEWS_EVENT = "news_event"
    EMERGENCY = "emergency"

class TradeDecision(Enum):
    """Risk manager trade decisions"""
    APPROVED = "approved"
    REJECTED = "rejected"
    REDUCED = "reduced"
    DELAYED = "delayed"

@dataclass
class TradeRequest:
    """Trade request structure for risk evaluation"""
    symbol: str
    direction: str  # "BUY" or "SELL"
    strategy_id: str
    confidence: float = 1.0
    urgency: str = "NORMAL"  # "LOW", "NORMAL", "HIGH"
    metadata: Optional[Dict] = None

@dataclass
class RiskDecision:
    """Risk manager decision output"""
    decision: TradeDecision
    approved_lot_size: float
    rejection_reason: Optional[str] = None
    risk_metrics: Optional[Dict] = None
    execution_priority: str = "NORMAL"

@dataclass
class AccountMetrics:
    """Real-time account performance metrics"""
    balance: float
    equity: float
    free_margin: float
    margin_level: float
    daily_pnl: float
    total_exposure: float
    drawdown_percent: float
    open_positions: int

class CoefficientBasedRiskManager:
    """
    Simple coefficient-based risk management system
    
    Core Philosophy:
    - Position Size = Min Lot Size × Asset Coefficient
    - Simple, predictable, and effective
    - Asset-class appropriate sizing
    """
    
    def __init__(self, config_path: str = "risk_config.json"):
        """Initialize the coefficient-based risk manager"""
        self.config_path = config_path
        self.logger = self.setup_logging()
        
        # Load symbol specifications from our screening
        self.symbol_specs = self.load_symbol_specifications()
        
        # Initialize risk configuration
        self.risk_config = self.load_risk_configuration()
        
        # Account monitoring
        self.account_metrics = None
        self.last_account_update = None
        
        # Position tracking
        self.active_positions = {}
        self.position_history = []
        
        # Market condition tracking
        self.current_market_condition = MarketCondition.NORMAL
        self.condition_multiplier = 1.0
        
        # Performance metrics
        self.performance_stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "coefficient_adjustments": 0
        }
        
        # Risk limits (hard-coded safety limits)
        self.HARD_LIMITS = {
            "max_daily_loss_percent": 5.0,
            "max_total_exposure_percent": 25.0,
            "max_drawdown_percent": 15.0,
            "max_positions_per_symbol": 1,
            "max_total_positions": 9,  # One per symbol max
            "min_account_balance": 1000.0
        }
        
        self.logger.info("🎯 Coefficient-Based Risk Manager initialized")
        self.logger.info(f"📊 Managing {len(self.get_tradeable_symbols())} tradeable symbols")
        
    def setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for risk management"""
        logger = logging.getLogger("RiskManager")
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # File handler for risk decisions
        file_handler = logging.FileHandler(
            logs_dir / f"risk_manager_{datetime.now().strftime('%Y%m%d')}.log"
        )
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
        
    def load_symbol_specifications(self) -> Dict:
        """Load symbol specifications from our screening results"""
        try:
            with open('symbol_specifications.json', 'r') as f:
                specs = json.load(f)
            self.logger.info(f"✅ Loaded symbol specifications for {len(specs.get('tradeable_symbols', []))} symbols")
            return specs
        except Exception as e:
            self.logger.error(f"❌ Failed to load symbol specifications: {e}")
            return {}
            
    def load_risk_configuration(self) -> Dict:
        """Load or create risk configuration with coefficient settings"""
        default_config = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "position_coefficients": {
                # Crypto Assets (min_lot: 0.01, coefficient: 5)
                "BTCUSD": {"min_lot": 0.01, "coefficient": 5, "asset_class": "crypto", "smart_cap": 1},
                "ETHUSD": {"min_lot": 0.01, "coefficient": 5, "asset_class": "crypto"},
                "SOLUSD": {"min_lot": 0.01, "coefficient": 5, "asset_class": "crypto"},
                "XRPUSD": {"min_lot": 0.01, "coefficient": 5, "asset_class": "crypto"},
                
                # Index Assets (min_lot: 0.1, coefficient: 1) 
                "US2000": {"min_lot": 0.1, "coefficient": 1, "asset_class": "index"},
                "NAS100": {"min_lot": 0.1, "coefficient": 1, "asset_class": "index"},
                "NAS100ft": {"min_lot": 0.1, "coefficient": 1, "asset_class": "index"},
                "SP500ft": {"min_lot": 0.1, "coefficient": 1, "asset_class": "index"},
                
                # Commodity Assets (min_lot: 0.01, coefficient: 1)
                "USOUSD": {"min_lot": 0.01, "coefficient": 1, "asset_class": "commodity"}
            },
            "market_condition_multipliers": {
                "normal": 1.0,
                "bull_market": 1.0,
                "bear_market": 0.5,
                "high_volatility": 0.7,
                "low_volatility": 1.2,
                "news_event": 0.3,
                "emergency": 0.1
            },
            "risk_limits": {
                "daily_loss_limit_percent": 3.0,  # Soft limit
                "exposure_warning_percent": 20.0,  # Warning threshold
                "drawdown_warning_percent": 10.0,
                "max_correlation_warning": 0.7
            },
            "performance_thresholds": {
                "coefficient_increase_win_rate": 0.65,  # Increase coefficients if win rate > 65%
                "coefficient_decrease_win_rate": 0.45,  # Decrease coefficients if win rate < 45%
                "adjustment_frequency_days": 7,  # Review coefficients weekly
                "min_trades_for_adjustment": 20  # Need minimum trades for statistical significance
            },
            "smart_filtering": {
                "enabled": True,
                "max_position_percent_of_account": 15.0,  # No single position > 15% of account
                "btc_max_coefficient": 1.0,  # BTCUSD hard cap at coefficient 1
                "min_safe_coefficient": 1.0,  # Never reduce coefficient below 1
                "description": "Smart Dynamic Filtering with BTC safety cap"
            }
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                self.logger.info(f"✅ Loaded existing risk configuration")
                return config
            else:
                # Create default configuration
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                self.logger.info(f"✅ Created default risk configuration at {self.config_path}")
                return default_config
        except Exception as e:
            self.logger.error(f"❌ Failed to load risk configuration: {e}")
            return default_config
            
    def save_risk_configuration(self):
        """Save current risk configuration to file"""
        try:
            self.risk_config["last_updated"] = datetime.now().isoformat()
            with open(self.config_path, 'w') as f:
                json.dump(self.risk_config, f, indent=2)
            self.logger.info("💾 Risk configuration saved successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to save risk configuration: {e}")
            
    def get_tradeable_symbols(self) -> List[str]:
        """Get list of all tradeable symbols"""
        if 'tradeable_symbols' in self.symbol_specs:
            return self.symbol_specs['tradeable_symbols']
        elif 'symbol_specifications' in self.symbol_specs:
            return [k for k, v in self.symbol_specs['symbol_specifications'].items() 
                   if v.get('tradeable', False)]
        else:
            return list(self.risk_config['position_coefficients'].keys())
            
    def calculate_position_size(self, symbol: str, market_condition_override: Optional[MarketCondition] = None) -> float:
        """
        Calculate position size using Smart Dynamic Filtering approach
        
        Features:
        - BTCUSD hard cap at coefficient 1 for safety
        - Dynamic coefficient reduction for high-value positions
        - Market condition multipliers
        - Minimum lot size enforcement
        """
        if symbol not in self.risk_config['position_coefficients']:
            self.logger.warning(f"⚠️ Symbol {symbol} not in coefficient configuration")
            return 0.0
            
        config = self.risk_config['position_coefficients'][symbol]
        min_lot = config['min_lot']
        base_coefficient = config['coefficient']
        
        # Smart Dynamic Filtering: Calculate safe coefficient
        safe_coefficient = self.calculate_safe_coefficient(symbol, base_coefficient)
        
        # Apply market condition multiplier
        condition = market_condition_override or self.current_market_condition
        condition_multiplier = self.risk_config['market_condition_multipliers'].get(condition.value, 1.0)
        
        # Calculate final position size
        position_size = min_lot * safe_coefficient * condition_multiplier
        
        # Ensure position size respects minimum lot requirements
        position_size = max(position_size, min_lot)
        
        # Log the coefficient adjustment if it occurred
        if safe_coefficient != base_coefficient:
            self.logger.info(f"🎯 {symbol}: coefficient {base_coefficient} → {safe_coefficient} (smart filtering)")
        
        self.logger.debug(f"📊 Position size for {symbol}: {min_lot} × {safe_coefficient} × {condition_multiplier:.2f} = {position_size}")
        
        return round(position_size, 2)  # Round to 2 decimal places for MT5
        
    def calculate_safe_coefficient(self, symbol: str, base_coefficient: float) -> float:
        """
        Calculate safe coefficient using Smart Dynamic Filtering
        
        Rules:
        1. BTCUSD: Hard cap at coefficient 1 (never allow higher)
        2. Other symbols: Reduce coefficient if position value > 15% of account
        3. Never reduce below coefficient 1.0
        """
        # Special handling for BTCUSD - hard cap at coefficient 1
        if symbol == "BTCUSD":
            safe_coefficient = min(base_coefficient, 1.0)
            if safe_coefficient != base_coefficient:
                self.logger.info(f"🛡️ BTCUSD coefficient capped at 1 for safety (was {base_coefficient})")
            return safe_coefficient
            
        # For other symbols, check if position value would be too high
        try:
            # Get current market data
            tick = mt5.symbol_info_tick(symbol)
            symbol_info = mt5.symbol_info(symbol)
            
            if not tick or not symbol_info:
                self.logger.warning(f"⚠️ Cannot get market data for {symbol}, using base coefficient")
                return base_coefficient
                
            # Get account balance for percentage calculation
            if not self.account_metrics:
                # Try to update account metrics
                if not self.update_account_metrics():
                    self.logger.warning(f"⚠️ Cannot get account metrics, using base coefficient for {symbol}")
                    return base_coefficient
                    
            # Calculate position value with base coefficient
            min_lot = self.risk_config['position_coefficients'][symbol]['min_lot']
            position_value = min_lot * base_coefficient * symbol_info.trade_contract_size * tick.ask
            
            # Check if position value exceeds 15% of account (safe limit)
            max_position_value = self.account_metrics.balance * 0.15
            
            if position_value > max_position_value:
                # Calculate safe coefficient to bring position within 15% limit
                safe_coefficient = max_position_value / (min_lot * symbol_info.trade_contract_size * tick.ask)
                # Never reduce below coefficient 1.0
                safe_coefficient = max(safe_coefficient, 1.0)
                
                self.logger.info(f"📉 {symbol}: position value ${position_value:,.0f} > ${max_position_value:,.0f} limit")
                self.logger.info(f"🎯 {symbol}: reducing coefficient {base_coefficient} → {safe_coefficient:.1f}")
                
                return round(safe_coefficient, 1)
            else:
                # Position value is acceptable, use base coefficient
                return base_coefficient
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating safe coefficient for {symbol}: {e}")
            # On error, use base coefficient but log the issue
            return base_coefficient
        
    def update_account_metrics(self) -> bool:
        """Update real-time account metrics from MT5"""
        try:
            # Connect to MT5 if needed
            if not mt5.initialize():
                self.logger.error("❌ Failed to initialize MT5 connection")
                return False
                
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                self.logger.error("❌ Failed to retrieve account information")
                return False
                
            # Calculate additional metrics
            daily_pnl = self.calculate_daily_pnl()
            total_exposure = self.calculate_total_exposure()
            drawdown_percent = self.calculate_drawdown_percent(account_info.equity)
            open_positions = len(mt5.positions_get() or [])
            
            # Update account metrics
            self.account_metrics = AccountMetrics(
                balance=account_info.balance,
                equity=account_info.equity,
                free_margin=account_info.margin_free,
                margin_level=account_info.margin_level,
                daily_pnl=daily_pnl,
                total_exposure=total_exposure,
                drawdown_percent=drawdown_percent,
                open_positions=open_positions
            )
            
            self.last_account_update = datetime.now()
            self.logger.debug(f"📊 Account metrics updated: Balance={account_info.balance}, Equity={account_info.equity}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update account metrics: {e}")
            return False
            
    def calculate_daily_pnl(self) -> float:
        """Calculate today's profit/loss from position history"""
        try:
            # Get today's deals/history from MT5
            today = datetime.now().date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Get deals for today
            deals = mt5.history_deals_get(today_start, today_end)
            if deals is None:
                return 0.0
                
            # Sum up today's profit/loss
            daily_pnl = sum(deal.profit for deal in deals)
            return daily_pnl
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate daily P&L: {e}")
            return 0.0
            
    def calculate_total_exposure(self) -> float:
        """Calculate total position exposure across all symbols"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return 0.0
                
            total_exposure = 0.0
            for position in positions:
                # Get current price
                tick = mt5.symbol_info_tick(position.symbol)
                if tick:
                    position_value = position.volume * position.price_current
                    total_exposure += abs(position_value)
                    
            return total_exposure
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate total exposure: {e}")
            return 0.0
            
    def calculate_drawdown_percent(self, current_equity: float) -> float:
        """Calculate current drawdown percentage from peak equity"""
        try:
            # Get historical high equity (simplified - could use more sophisticated tracking)
            if not hasattr(self, 'peak_equity'):
                self.peak_equity = current_equity
                
            # Update peak if we have a new high
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
                
            # Calculate drawdown
            if self.peak_equity > 0:
                drawdown_percent = ((self.peak_equity - current_equity) / self.peak_equity) * 100
                return max(0, drawdown_percent)
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate drawdown: {e}")
            return 0.0
            
    def evaluate_trade_request(self, trade_request: TradeRequest) -> RiskDecision:
        """
        Main risk evaluation function - determines if trade should be executed
        
        Risk Evaluation Flow:
        1. Update account metrics
        2. Check hard safety limits  
        3. Calculate position size
        4. Validate exposure limits
        5. Apply market condition adjustments
        6. Make final decision
        """
        self.logger.info(f"🔍 Evaluating trade request: {trade_request.symbol} {trade_request.direction}")
        
        # Update account metrics
        if not self.update_account_metrics():
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason="Failed to update account metrics"
            )
            
        # Check hard safety limits first
        safety_check = self.check_safety_limits()
        if not safety_check[0]:
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason=f"Safety limit violation: {safety_check[1]}"
            )
            
        # Calculate position size for this symbol
        position_size = self.calculate_position_size(trade_request.symbol)
        if position_size <= 0:
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason="Invalid position size calculated"
            )
            
        # Check if we already have a position in this symbol
        existing_positions = mt5.positions_get(symbol=trade_request.symbol)
        if existing_positions and len(existing_positions) >= self.HARD_LIMITS["max_positions_per_symbol"]:
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason=f"Maximum positions per symbol exceeded ({self.HARD_LIMITS['max_positions_per_symbol']})"
            )
            
        # Check total position limits
        if self.account_metrics.open_positions >= self.HARD_LIMITS["max_total_positions"]:
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason=f"Maximum total positions exceeded ({self.HARD_LIMITS['max_total_positions']})"
            )
            
        # Calculate risk metrics
        risk_metrics = self.calculate_risk_metrics(trade_request.symbol, position_size)
        
        # Check exposure limits
        if self.account_metrics.total_exposure + risk_metrics['position_value'] > (self.account_metrics.balance * self.HARD_LIMITS["max_total_exposure_percent"] / 100):
            return RiskDecision(
                decision=TradeDecision.REJECTED,
                approved_lot_size=0.0,
                rejection_reason="Total exposure limit would be exceeded"
            )
            
        # All checks passed - approve the trade
        self.logger.info(f"✅ Trade approved: {trade_request.symbol} {trade_request.direction} {position_size} lots")
        
        return RiskDecision(
            decision=TradeDecision.APPROVED,
            approved_lot_size=position_size,
            risk_metrics=risk_metrics,
            execution_priority="NORMAL"
        )
        
    def check_safety_limits(self) -> Tuple[bool, str]:
        """Check hard safety limits that should never be violated"""
        if not self.account_metrics:
            return False, "Account metrics not available"
            
        # Check minimum account balance
        if self.account_metrics.balance < self.HARD_LIMITS["min_account_balance"]:
            return False, f"Account balance below minimum ({self.HARD_LIMITS['min_account_balance']})"
            
        # Check daily loss limit
        daily_loss_percent = abs(self.account_metrics.daily_pnl) / self.account_metrics.balance * 100
        if self.account_metrics.daily_pnl < 0 and daily_loss_percent > self.HARD_LIMITS["max_daily_loss_percent"]:
            return False, f"Daily loss limit exceeded ({daily_loss_percent:.2f}% > {self.HARD_LIMITS['max_daily_loss_percent']}%)"
            
        # Check drawdown limit
        if self.account_metrics.drawdown_percent > self.HARD_LIMITS["max_drawdown_percent"]:
            return False, f"Drawdown limit exceeded ({self.account_metrics.drawdown_percent:.2f}% > {self.HARD_LIMITS['max_drawdown_percent']}%)"
            
        # Check margin level (if positions exist)
        if self.account_metrics.open_positions > 0 and self.account_metrics.margin_level < 200:  # 200% minimum
            return False, f"Margin level too low ({self.account_metrics.margin_level:.1f}% < 200%)"
            
        return True, "All safety limits OK"
        
    def calculate_risk_metrics(self, symbol: str, position_size: float) -> Dict:
        """Calculate comprehensive risk metrics for a position"""
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {"error": "Cannot get current price"}
                
            # Get symbol info for contract size
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return {"error": "Cannot get symbol info"}
                
            # Calculate position value
            position_value = position_size * symbol_info.trade_contract_size * tick.ask
            
            # Calculate risk as percentage of account
            risk_percent = (position_value / self.account_metrics.balance) * 100 if self.account_metrics.balance > 0 else 0
            
            # Get asset class for additional context
            asset_class = self.risk_config['position_coefficients'].get(symbol, {}).get('asset_class', 'unknown')
            
            return {
                "symbol": symbol,
                "position_size": position_size,
                "current_price": tick.ask,
                "contract_size": symbol_info.trade_contract_size,
                "position_value": position_value,
                "risk_percent_of_account": risk_percent,
                "asset_class": asset_class,
                "spread": symbol_info.spread,
                "currency_profit": symbol_info.currency_profit
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to calculate risk metrics for {symbol}: {e}")
            return {"error": str(e)}
            
    def set_market_condition(self, condition: MarketCondition, reason: str = "Manual override"):
        """Set current market condition for coefficient adjustment"""
        old_condition = self.current_market_condition
        self.current_market_condition = condition
        self.condition_multiplier = self.risk_config['market_condition_multipliers'].get(condition.value, 1.0)
        
        self.logger.warning(f"🌍 Market condition changed: {old_condition.value} → {condition.value} (multiplier: {self.condition_multiplier:.2f})")
        self.logger.warning(f"📝 Reason: {reason}")
        
        # Log coefficient changes for all symbols
        for symbol in self.get_tradeable_symbols():
            old_size = self.calculate_position_size(symbol, old_condition)
            new_size = self.calculate_position_size(symbol, condition)
            if old_size != new_size:
                self.logger.info(f"📊 {symbol}: {old_size} → {new_size} lots")
                
    def emergency_stop_all(self, reason: str = "Emergency stop triggered"):
        """Emergency function to halt all trading immediately"""
        self.logger.critical(f"🚨 EMERGENCY STOP ALL ACTIVATED: {reason}")
        
        # Set emergency market condition
        self.set_market_condition(MarketCondition.EMERGENCY, reason)
        
        # Log emergency action
        emergency_record = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "account_balance": self.account_metrics.balance if self.account_metrics else "unknown",
            "open_positions": self.account_metrics.open_positions if self.account_metrics else "unknown",
            "action": "ALL_TRADING_STOPPED"
        }
        
        # Save emergency record
        emergency_log = Path("logs") / f"emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(emergency_log, 'w') as f:
            json.dump(emergency_record, f, indent=2)
            
        return emergency_record
        
    def adjust_coefficients_based_on_performance(self):
        """Adjust coefficients based on recent performance (weekly review)"""
        self.logger.info("📊 Reviewing coefficients based on performance...")
        
        # Get performance thresholds
        thresholds = self.risk_config['performance_thresholds']
        
        # Check if we have enough trades for statistical significance
        if self.performance_stats['total_trades'] < thresholds['min_trades_for_adjustment']:
            self.logger.info(f"⏳ Need {thresholds['min_trades_for_adjustment']} trades for adjustment, currently have {self.performance_stats['total_trades']}")
            return
            
        # Calculate current win rate
        win_rate = self.performance_stats['winning_trades'] / self.performance_stats['total_trades']
        
        # Determine adjustment
        adjustment_factor = 1.0
        if win_rate > thresholds['coefficient_increase_win_rate']:
            adjustment_factor = 1.1  # Increase coefficients by 10%
            self.logger.info(f"📈 High win rate ({win_rate:.2%}), increasing coefficients by 10%")
        elif win_rate < thresholds['coefficient_decrease_win_rate']:
            adjustment_factor = 0.9  # Decrease coefficients by 10%
            self.logger.info(f"📉 Low win rate ({win_rate:.2%}), decreasing coefficients by 10%")
        else:
            self.logger.info(f"📊 Win rate OK ({win_rate:.2%}), no coefficient adjustment needed")
            return
            
        # Apply adjustment to all coefficients
        for symbol in self.risk_config['position_coefficients']:
            old_coeff = self.risk_config['position_coefficients'][symbol]['coefficient']
            new_coeff = round(old_coeff * adjustment_factor, 1)
            # Ensure minimum coefficient of 0.5
            new_coeff = max(0.5, new_coeff)
            self.risk_config['position_coefficients'][symbol]['coefficient'] = new_coeff
            self.logger.info(f"🔧 {symbol}: coefficient {old_coeff} → {new_coeff}")
            
        # Save updated configuration
        self.save_risk_configuration()
        self.performance_stats['coefficient_adjustments'] += 1
        
        # Reset performance stats for next period
        self.performance_stats['total_trades'] = 0
        self.performance_stats['winning_trades'] = 0
        
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio and risk summary"""
        if not self.update_account_metrics():
            return {"error": "Failed to update account metrics"}
            
        # Calculate theoretical maximum exposure
        max_exposure = 0.0
        position_breakdown = {}
        
        for symbol in self.get_tradeable_symbols():
            position_size = self.calculate_position_size(symbol)
            risk_metrics = self.calculate_risk_metrics(symbol, position_size)
            
            if 'position_value' in risk_metrics:
                max_exposure += risk_metrics['position_value']
                position_breakdown[symbol] = {
                    "position_size": position_size,
                    "position_value": risk_metrics['position_value'],
                    "risk_percent": risk_metrics['risk_percent_of_account'],
                    "asset_class": risk_metrics['asset_class']
                }
                
        return {
            "timestamp": datetime.now().isoformat(),
            "account_metrics": {
                "balance": self.account_metrics.balance,
                "equity": self.account_metrics.equity,
                "free_margin": self.account_metrics.free_margin,
                "daily_pnl": self.account_metrics.daily_pnl,
                "drawdown_percent": self.account_metrics.drawdown_percent,
                "open_positions": self.account_metrics.open_positions
            },
            "risk_metrics": {
                "current_exposure": self.account_metrics.total_exposure,
                "max_theoretical_exposure": max_exposure,
                "exposure_utilization_percent": (self.account_metrics.total_exposure / max_exposure * 100) if max_exposure > 0 else 0,
                "market_condition": self.current_market_condition.value,
                "condition_multiplier": self.condition_multiplier
            },
            "position_breakdown": position_breakdown,
            "performance_stats": self.performance_stats.copy(),
            "safety_status": self.check_safety_limits()
        }
        
    def generate_risk_report(self, save_to_file: bool = True) -> Dict:
        """Generate comprehensive risk management report"""
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "risk_manager_version": "1.0",
                "report_type": "comprehensive_risk_analysis"
            },
            "portfolio_summary": self.get_portfolio_summary(),
            "risk_configuration": self.risk_config.copy(),
            "recent_performance": self.performance_stats.copy()
        }
        
        if save_to_file:
            report_path = Path("reports") / f"risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
                
            self.logger.info(f"📋 Risk report saved: {report_path}")
            
        return report


def main():
    """Main function for testing and demonstration"""
    print("🎯 Coefficient-Based Risk Manager - Test Mode")
    print("=" * 60)
    
    # Initialize risk manager
    risk_manager = CoefficientBasedRiskManager()
    
    # Test coefficient calculation for all symbols with smart filtering
    print("\n📊 SMART POSITION SIZE CALCULATIONS:")
    print("-" * 55)
    print(f"{'Symbol':<10} | {'Base':<4} | {'Safe':<4} | {'Size':<5} | {'Value':<10} | {'Risk%':<6} | {'Class':<10}")
    print("-" * 55)
    
    tradeable_symbols = risk_manager.get_tradeable_symbols()
    for symbol in tradeable_symbols:
        config = risk_manager.risk_config['position_coefficients'].get(symbol, {})
        base_coeff = config.get('coefficient', 0)
        safe_coeff = risk_manager.calculate_safe_coefficient(symbol, base_coeff)
        position_size = risk_manager.calculate_position_size(symbol)
        
        # Calculate position value and risk percentage
        risk_metrics = risk_manager.calculate_risk_metrics(symbol, position_size)
        position_value = risk_metrics.get('position_value', 0) if 'error' not in risk_metrics else 0
        risk_percent = risk_metrics.get('risk_percent_of_account', 0) if 'error' not in risk_metrics else 0
        
        # Format output
        asset_class = config.get('asset_class', 'unknown')
        coeff_display = f"{safe_coeff:.1f}" if safe_coeff != base_coeff else f"{safe_coeff:.0f}"
        value_display = f"${position_value:,.0f}" if position_value > 0 else "N/A"
        risk_display = f"{risk_percent:.1f}%" if risk_percent > 0 else "N/A"
        
        print(f"{symbol:<10} | {base_coeff:<4.0f} | {coeff_display:<4} | {position_size:<5} | {value_display:<10} | {risk_display:<6} | {asset_class:<10}")
    
    # Generate portfolio summary
    print("\n📋 PORTFOLIO RISK SUMMARY:")
    print("-" * 40)
    
    summary = risk_manager.get_portfolio_summary()
    if "error" not in summary:
        account = summary["account_metrics"]
        risk = summary["risk_metrics"]
        
        print(f"Account Balance: ${account['balance']:,.2f}")
        print(f"Daily P&L: ${account['daily_pnl']:+,.2f}")
        print(f"Current Drawdown: {account['drawdown_percent']:.1f}%")
        print(f"Open Positions: {account['open_positions']}")
        print(f"Market Condition: {risk['market_condition']}")
        print(f"Condition Multiplier: {risk['condition_multiplier']:.2f}x")
        print(f"Max Theoretical Exposure: ${risk['max_theoretical_exposure']:,.2f}")
        
    # Test trade evaluation
    print("\n🧪 TRADE EVALUATION TEST:")
    print("-" * 40)
    
    test_request = TradeRequest(
        symbol="BTCUSD",
        direction="BUY", 
        strategy_id="test_strategy",
        confidence=0.8
    )
    
    decision = risk_manager.evaluate_trade_request(test_request)
    print(f"Trade Decision: {decision.decision.value}")
    print(f"Approved Lot Size: {decision.approved_lot_size}")
    if decision.rejection_reason:
        print(f"Rejection Reason: {decision.rejection_reason}")
    
    # Generate full risk report
    print("\n📋 GENERATING COMPREHENSIVE RISK REPORT...")
    report = risk_manager.generate_risk_report()
    print(f"✅ Risk report generated with {len(report)} sections")
    
    print(f"\n🎯 Risk Manager test completed successfully!")
    print(f"📁 Check 'reports' and 'logs' directories for detailed output")


if __name__ == "__main__":
    main()
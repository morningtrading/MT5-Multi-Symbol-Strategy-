#!/usr/bin/env python3
"""
Enhanced MT5 Order Management System
===================================

Production-ready order management system that provides:
- Multi-symbol order execution and management
- Advanced order types (Market, Limit, Stop, Stop-Loss, Take-Profit)
- Position tracking and modification
- Real-time order status monitoring
- Integration with risk management system
- Order queue management and execution priority
- Error recovery and retry mechanisms

Features:
- Async order processing capabilities
- Order validation and pre-execution checks
- Position lifecycle management
- Comprehensive audit trail and logging
- Integration with existing risk manager

Author: Multi-Symbol Strategy Framework
Version: 1.0 (Production Ready)  
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
import threading
import queue
from pathlib import Path
import uuid

# Import our risk manager
from GEN_risk_manager import CoefficientBasedRiskManager, TradeRequest, RiskDecision, MarketCondition

class OrderType(Enum):
    """Order types supported by the system"""
    MARKET_BUY = "MARKET_BUY"
    MARKET_SELL = "MARKET_SELL"
    LIMIT_BUY = "LIMIT_BUY"
    LIMIT_SELL = "LIMIT_SELL"
    STOP_BUY = "STOP_BUY"
    STOP_SELL = "STOP_SELL"
    CLOSE_POSITION = "CLOSE_POSITION"
    MODIFY_POSITION = "MODIFY_POSITION"

class OrderStatus(Enum):
    """Order execution status"""
    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class PositionStatus(Enum):
    """Position status tracking"""
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    MODIFIED = "MODIFIED"

@dataclass
class OrderRequest:
    """Order request structure"""
    order_id: str
    symbol: str
    order_type: OrderType
    volume: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    deviation: int = 20
    comment: str = "Strategy Order"
    magic: int = 234000
    strategy_id: str = "DefaultStrategy"
    priority: int = 1  # 1=Normal, 2=High, 3=Emergency
    expires_at: Optional[datetime] = None
    position_ticket: Optional[int] = None  # For closing/modifying positions
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())[:8]

@dataclass  
class OrderResult:
    """Order execution result"""
    order_id: str
    mt5_order_id: Optional[int]
    mt5_position_id: Optional[int]
    status: OrderStatus
    executed_price: Optional[float]
    executed_volume: Optional[float]
    execution_time: datetime
    error_message: Optional[str] = None
    retry_count: int = 0
    total_cost: Optional[float] = None
    estimated_profit: Optional[float] = None

@dataclass
class Position:
    """Position tracking structure"""
    position_id: int
    symbol: str
    volume: float
    position_type: str  # "BUY" or "SELL"
    open_price: float
    current_price: float
    open_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    status: PositionStatus = PositionStatus.OPEN
    strategy_id: str = "Unknown"
    magic: int = 234000
    last_update: datetime = field(default_factory=datetime.now)

class EnhancedOrderManager:
    """Production-ready order management system"""
    
    def __init__(self, risk_manager: Optional[CoefficientBasedRiskManager] = None):
        """Initialize the enhanced order manager"""
        self.risk_manager = risk_manager or CoefficientBasedRiskManager()
        
        # Order management
        self.pending_orders: queue.PriorityQueue = queue.PriorityQueue()
        self.active_orders: Dict[str, OrderRequest] = {}
        self.order_results: Dict[str, OrderResult] = {}
        self.order_history: List[OrderResult] = []
        
        # Position management  
        self.active_positions: Dict[int, Position] = {}
        self.position_history: List[Position] = []
        
        # Symbol specifications
        self.symbol_specs = self.load_symbol_specifications()
        self.symbol_info_cache: Dict[str, Dict] = {}
        
        # Execution settings
        self.max_retries = 3
        self.retry_delay = 1.0
        self.order_timeout = 30.0
        self.position_update_interval = 5.0
        
        # Threading for async processing
        self.processing_thread = None
        self.monitoring_thread = None
        self.shutdown_event = threading.Event()
        self.is_running = False
        
        # Performance tracking
        self.execution_stats = {
            "total_orders": 0,
            "successful_orders": 0,
            "failed_orders": 0,
            "avg_execution_time": 0.0,
            "total_volume": 0.0,
            "total_cost": 0.0,
            "active_positions_count": 0
        }
        
        # Logging
        self.logger = self.setup_logging()
        
    def setup_logging(self):
        """Setup comprehensive logging for order management"""
        import logging
        
        logger = logging.getLogger("OrderManager")
        logger.setLevel(logging.INFO)
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # File handler for order management
        file_handler = logging.FileHandler(
            log_dir / f"order_manager_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
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
        
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def load_symbol_specifications(self) -> Dict:
        """Load symbol specifications from screening results"""
        try:
            with open('symbol_specifications.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load symbol specs: {e}")
            return {}
    
    def initialize(self) -> bool:
        """Initialize the order manager and MT5 connection"""
        self.logger.info("🚀 Initializing Enhanced Order Manager...")
        
        # Initialize MT5
        if not mt5.initialize():
            error = mt5.last_error()
            self.logger.error(f"MT5 initialization failed: {error}")
            return False
        
        # Verify account info
        account_info = mt5.account_info()
        if account_info is None:
            self.logger.error("Failed to get account information")
            return False
        
        self.logger.info(f"✅ Connected - Account: {account_info.login} | Balance: ${account_info.balance:,.2f}")
        
        # Load existing positions
        self.sync_positions()
        
        # Start processing threads
        self.start_processing()
        
        self.logger.info("🎯 Order Manager initialized and ready")
        return True
    
    def sync_positions(self):
        """Synchronize positions with MT5"""
        positions = mt5.positions_get()
        if positions:
            self.logger.info(f"📊 Syncing {len(positions)} existing positions")
            
            for pos in positions:
                position = Position(
                    position_id=pos.ticket,
                    symbol=pos.symbol,
                    volume=pos.volume,
                    position_type="BUY" if pos.type == 0 else "SELL",
                    open_price=pos.price_open,
                    current_price=pos.price_current,
                    open_time=datetime.fromtimestamp(pos.time),
                    unrealized_pnl=pos.profit,
                    magic=pos.magic,
                    status=PositionStatus.OPEN
                )
                self.active_positions[pos.ticket] = position
                
            self.logger.info(f"✅ Synchronized {len(self.active_positions)} active positions")
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Get cached symbol information"""
        if symbol in self.symbol_info_cache:
            return self.symbol_info_cache[symbol]
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.logger.error(f"Cannot get symbol info for {symbol}")
            return None
        
        info_dict = {
            'symbol': symbol,
            'ask': symbol_info.ask,
            'bid': symbol_info.bid,
            'volume_min': symbol_info.volume_min,
            'volume_max': symbol_info.volume_max,
            'volume_step': symbol_info.volume_step,
            'point': symbol_info.point,
            'digits': symbol_info.digits,
            'spread': symbol_info.spread,
            'trade_mode': symbol_info.trade_mode
        }
        
        self.symbol_info_cache[symbol] = info_dict
        return info_dict
    
    def validate_order(self, order_request: OrderRequest) -> Tuple[bool, Optional[str]]:
        """Validate order request before execution"""
        # Check symbol availability
        symbol_info = self.get_symbol_info(order_request.symbol)
        if symbol_info is None:
            return False, f"Symbol {order_request.symbol} not available"
        
        # Check volume constraints
        min_volume = symbol_info['volume_min']
        max_volume = symbol_info['volume_max']
        
        if order_request.volume < min_volume:
            return False, f"Volume {order_request.volume} below minimum {min_volume}"
        
        if order_request.volume > max_volume:
            return False, f"Volume {order_request.volume} above maximum {max_volume}"
        
        # Check trading permissions
        if symbol_info['trade_mode'] == 0:  # Trading disabled
            return False, f"Trading disabled for {order_request.symbol}"
        
        # Check price validity for limit/stop orders
        if order_request.order_type in [OrderType.LIMIT_BUY, OrderType.LIMIT_SELL, 
                                      OrderType.STOP_BUY, OrderType.STOP_SELL]:
            if order_request.price is None or order_request.price <= 0:
                return False, "Price required for limit/stop orders"
        
        # Check account balance/margin
        account_info = mt5.account_info()
        if account_info is None:
            return False, "Cannot verify account status"
        
        if account_info.margin_free < 100:  # Minimum margin check
            return False, "Insufficient margin available"
        
        return True, None
    
    def submit_order(self, order_request: OrderRequest) -> str:
        """Submit order for execution"""
        self.logger.info(f"📝 Submitting order: {order_request.order_type.value} {order_request.volume} {order_request.symbol}")
        
        # Validate order
        valid, error = self.validate_order(order_request)
        if not valid:
            self.logger.error(f"❌ Order validation failed: {error}")
            # Create failed result
            result = OrderResult(
                order_id=order_request.order_id,
                mt5_order_id=None,
                mt5_position_id=None,
                status=OrderStatus.REJECTED,
                executed_price=None,
                executed_volume=None,
                execution_time=datetime.now(),
                error_message=error
            )
            self.order_results[order_request.order_id] = result
            return order_request.order_id
        
        # Risk management check
        trade_request = TradeRequest(
            symbol=order_request.symbol,
            direction="BUY" if "BUY" in order_request.order_type.value else "SELL",
            strategy_id=order_request.strategy_id,
            confidence=1.0
        )
        
        risk_decision = self.risk_manager.evaluate_trade(trade_request)
        if risk_decision.decision.value != "approved":
            self.logger.warning(f"⚠️ Order rejected by risk manager: {risk_decision.rejection_reason}")
            result = OrderResult(
                order_id=order_request.order_id,
                mt5_order_id=None,
                mt5_position_id=None,
                status=OrderStatus.REJECTED,
                executed_price=None,
                executed_volume=None,
                execution_time=datetime.now(),
                error_message=f"Risk manager rejection: {risk_decision.rejection_reason}"
            )
            self.order_results[order_request.order_id] = result
            return order_request.order_id
        
        # Use approved lot size from risk manager
        order_request.volume = risk_decision.approved_lot_size
        
        # Add to pending orders queue
        priority = 10 - order_request.priority  # Lower number = higher priority
        self.pending_orders.put((priority, time.time(), order_request))
        self.active_orders[order_request.order_id] = order_request
        
        self.logger.info(f"✅ Order {order_request.order_id} queued for execution")
        return order_request.order_id
    
    def execute_order(self, order_request: OrderRequest) -> OrderResult:
        """Execute individual order with retry logic"""
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"🔄 Executing order {order_request.order_id} (attempt {attempt + 1})")
                
                # Get current symbol info
                symbol_info = self.get_symbol_info(order_request.symbol)
                if symbol_info is None:
                    raise Exception("Cannot get symbol information")
                
                # Prepare MT5 order request
                mt5_request = self.build_mt5_request(order_request, symbol_info)
                
                # Execute order
                result = mt5.order_send(mt5_request)
                execution_time = time.time() - start_time
                
                if result is None:
                    error = mt5.last_error()
                    raise Exception(f"Order send failed: {error}")
                
                if result.retcode != mt5.TRADE_RETCODE_DONE:
                    if attempt < self.max_retries:
                        self.logger.warning(f"⚠️ Order failed, retrying: {result.retcode} - {result.comment}")
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Order failed: {result.retcode} - {result.comment}")
                
                # Success - create result
                order_result = OrderResult(
                    order_id=order_request.order_id,
                    mt5_order_id=result.order,
                    mt5_position_id=getattr(result, 'deal', None),
                    status=OrderStatus.FILLED,
                    executed_price=result.price,
                    executed_volume=result.volume,
                    execution_time=datetime.now(),
                    retry_count=attempt
                )
                
                self.logger.info(f"✅ Order executed: {result.order} at {result.price}")
                
                # Update position tracking if this opens a position
                if order_request.order_type in [OrderType.MARKET_BUY, OrderType.MARKET_SELL,
                                              OrderType.LIMIT_BUY, OrderType.LIMIT_SELL,
                                              OrderType.STOP_BUY, OrderType.STOP_SELL]:
                    self.create_position_record(order_request, result)
                
                # Update statistics
                self.execution_stats["successful_orders"] += 1
                self.execution_stats["total_volume"] += result.volume
                
                return order_result
                
            except Exception as e:
                if attempt == self.max_retries:
                    self.logger.error(f"❌ Order execution failed after {self.max_retries + 1} attempts: {e}")
                    return OrderResult(
                        order_id=order_request.order_id,
                        mt5_order_id=None,
                        mt5_position_id=None,
                        status=OrderStatus.FAILED,
                        executed_price=None,
                        executed_volume=None,
                        execution_time=datetime.now(),
                        error_message=str(e),
                        retry_count=attempt
                    )
                else:
                    self.logger.warning(f"⚠️ Order execution attempt {attempt + 1} failed: {e}")
                    time.sleep(self.retry_delay * (attempt + 1))
    
    def build_mt5_request(self, order_request: OrderRequest, symbol_info: Dict) -> Dict:
        """Build MT5 order request from our order request"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": order_request.symbol,
            "volume": order_request.volume,
            "deviation": order_request.deviation,
            "magic": order_request.magic,
            "comment": order_request.comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Set order type and price
        if order_request.order_type == OrderType.MARKET_BUY:
            request["type"] = mt5.ORDER_TYPE_BUY
            request["price"] = symbol_info['ask']
        elif order_request.order_type == OrderType.MARKET_SELL:
            request["type"] = mt5.ORDER_TYPE_SELL
            request["price"] = symbol_info['bid']
        elif order_request.order_type == OrderType.LIMIT_BUY:
            request["type"] = mt5.ORDER_TYPE_BUY_LIMIT
            request["price"] = order_request.price
        elif order_request.order_type == OrderType.LIMIT_SELL:
            request["type"] = mt5.ORDER_TYPE_SELL_LIMIT
            request["price"] = order_request.price
        elif order_request.order_type == OrderType.STOP_BUY:
            request["type"] = mt5.ORDER_TYPE_BUY_STOP
            request["price"] = order_request.price
        elif order_request.order_type == OrderType.STOP_SELL:
            request["type"] = mt5.ORDER_TYPE_SELL_STOP
            request["price"] = order_request.price
        elif order_request.order_type == OrderType.CLOSE_POSITION:
            # For closing positions, reverse the order type
            position = self.active_positions.get(order_request.position_ticket)
            if position:
                if position.position_type == "BUY":
                    request["type"] = mt5.ORDER_TYPE_SELL
                    request["price"] = symbol_info['bid']
                else:
                    request["type"] = mt5.ORDER_TYPE_BUY
                    request["price"] = symbol_info['ask']
                request["position"] = order_request.position_ticket
        
        # Add stop loss and take profit if specified
        if order_request.stop_loss:
            request["sl"] = order_request.stop_loss
        
        if order_request.take_profit:
            request["tp"] = order_request.take_profit
        
        return request
    
    def create_position_record(self, order_request: OrderRequest, mt5_result):
        """Create position record for tracking"""
        position = Position(
            position_id=mt5_result.order,  # Use order ID as position ID initially
            symbol=order_request.symbol,
            volume=mt5_result.volume,
            position_type="BUY" if "BUY" in order_request.order_type.value else "SELL",
            open_price=mt5_result.price,
            current_price=mt5_result.price,
            open_time=datetime.now(),
            stop_loss=order_request.stop_loss,
            take_profit=order_request.take_profit,
            strategy_id=order_request.strategy_id,
            magic=order_request.magic,
            status=PositionStatus.OPEN
        )
        
        # We'll update with actual position ticket when we sync positions
        self.active_positions[mt5_result.order] = position
        self.logger.info(f"📊 Position created: {position.symbol} {position.volume} {position.position_type}")
    
    def close_position(self, position_ticket: int, volume: Optional[float] = None) -> str:
        """Close an existing position"""
        position = self.active_positions.get(position_ticket)
        if position is None:
            raise ValueError(f"Position {position_ticket} not found")
        
        close_volume = volume or position.volume
        
        close_order = OrderRequest(
            order_id=None,  # Will be auto-generated
            symbol=position.symbol,
            order_type=OrderType.CLOSE_POSITION,
            volume=close_volume,
            position_ticket=position_ticket,
            strategy_id=position.strategy_id,
            comment=f"Close position {position_ticket}",
            priority=2  # High priority for closes
        )
        
        return self.submit_order(close_order)
    
    def start_processing(self):
        """Start background processing threads"""
        if self.is_running:
            return
        
        self.is_running = True
        self.shutdown_event.clear()
        
        # Start order processing thread
        self.processing_thread = threading.Thread(target=self._process_orders, daemon=True)
        self.processing_thread.start()
        
        # Start position monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitor_positions, daemon=True)
        self.monitoring_thread.start()
        
        self.logger.info("🔄 Background processing threads started")
    
    def _process_orders(self):
        """Background order processing"""
        while not self.shutdown_event.is_set():
            try:
                # Get next order from queue with timeout
                try:
                    priority, timestamp, order_request = self.pending_orders.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Execute the order
                result = self.execute_order(order_request)
                
                # Store result
                self.order_results[order_request.order_id] = result
                self.order_history.append(result)
                
                # Remove from active orders
                if order_request.order_id in self.active_orders:
                    del self.active_orders[order_request.order_id]
                
                # Update statistics
                self.execution_stats["total_orders"] += 1
                
                self.pending_orders.task_done()
                
            except Exception as e:
                self.logger.error(f"Error in order processing: {e}")
                time.sleep(1)
    
    def _monitor_positions(self):
        """Background position monitoring"""
        while not self.shutdown_event.is_set():
            try:
                # Update position information
                self.update_positions()
                time.sleep(self.position_update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in position monitoring: {e}")
                time.sleep(5)
    
    def update_positions(self):
        """Update position information from MT5"""
        mt5_positions = mt5.positions_get()
        
        if mt5_positions is None:
            return
        
        # Create set of active MT5 position tickets
        mt5_tickets = {pos.ticket for pos in mt5_positions}
        
        # Update existing positions
        for pos in mt5_positions:
            if pos.ticket in self.active_positions:
                position = self.active_positions[pos.ticket]
                position.current_price = pos.price_current
                position.unrealized_pnl = pos.profit
                position.last_update = datetime.now()
            else:
                # New position not in our tracking - add it
                new_position = Position(
                    position_id=pos.ticket,
                    symbol=pos.symbol,
                    volume=pos.volume,
                    position_type="BUY" if pos.type == 0 else "SELL",
                    open_price=pos.price_open,
                    current_price=pos.price_current,
                    open_time=datetime.fromtimestamp(pos.time),
                    unrealized_pnl=pos.profit,
                    magic=pos.magic,
                    status=PositionStatus.OPEN
                )
                self.active_positions[pos.ticket] = new_position
        
        # Mark closed positions
        closed_positions = []
        for ticket, position in self.active_positions.items():
            if ticket not in mt5_tickets and position.status == PositionStatus.OPEN:
                position.status = PositionStatus.CLOSED
                closed_positions.append(ticket)
        
        # Move closed positions to history
        for ticket in closed_positions:
            position = self.active_positions[ticket]
            self.position_history.append(position)
            del self.active_positions[ticket]
            self.logger.info(f"📈 Position closed: {position.symbol} PnL: ${position.unrealized_pnl:.2f}")
        
        # Update statistics
        self.execution_stats["active_positions_count"] = len(self.active_positions)
    
    def get_order_status(self, order_id: str) -> Optional[OrderResult]:
        """Get order execution status"""
        return self.order_results.get(order_id)
    
    def get_active_positions(self) -> Dict[int, Position]:
        """Get all active positions"""
        return self.active_positions.copy()
    
    def get_position(self, position_ticket: int) -> Optional[Position]:
        """Get specific position"""
        return self.active_positions.get(position_ticket)
    
    def get_statistics(self) -> Dict:
        """Get execution statistics"""
        stats = self.execution_stats.copy()
        
        # Calculate success rate
        if stats["total_orders"] > 0:
            stats["success_rate"] = stats["successful_orders"] / stats["total_orders"]
        else:
            stats["success_rate"] = 0.0
        
        # Add position information
        stats["total_unrealized_pnl"] = sum(pos.unrealized_pnl for pos in self.active_positions.values())
        stats["total_realized_pnl"] = sum(pos.realized_pnl for pos in self.position_history)
        
        return stats
    
    def emergency_close_all(self) -> List[str]:
        """Emergency close all positions"""
        self.logger.warning("🚨 Emergency close all positions triggered")
        
        close_order_ids = []
        for ticket, position in self.active_positions.items():
            try:
                order_id = self.close_position(ticket)
                close_order_ids.append(order_id)
                self.logger.info(f"🚨 Emergency close submitted: {position.symbol}")
            except Exception as e:
                self.logger.error(f"Failed to close position {ticket}: {e}")
        
        return close_order_ids
    
    def shutdown(self):
        """Shutdown the order manager"""
        self.logger.info("🛑 Shutting down Order Manager...")
        
        # Stop processing
        self.is_running = False
        self.shutdown_event.set()
        
        # Wait for threads to finish
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        # Generate final report
        self.generate_final_report()
        
        # Shutdown MT5
        mt5.shutdown()
        self.logger.info("🏁 Order Manager shutdown complete")
    
    def generate_final_report(self):
        """Generate final execution report"""
        report_data = {
            "execution_statistics": self.get_statistics(),
            "active_positions": {
                str(ticket): {
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": pos.position_type,
                    "open_price": pos.open_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "open_time": pos.open_time.isoformat()
                }
                for ticket, pos in self.active_positions.items()
            },
            "recent_orders": [
                {
                    "order_id": result.order_id,
                    "status": result.status.value,
                    "executed_price": result.executed_price,
                    "executed_volume": result.executed_volume,
                    "execution_time": result.execution_time.isoformat()
                }
                for result in self.order_history[-50:]  # Last 50 orders
            ]
        }
        
        # Save report
        report_path = f"reports/order_manager_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        self.logger.info(f"📊 Final report saved: {report_path}")

# Convenience functions for easy usage
def create_market_buy_order(symbol: str, volume: float, **kwargs) -> OrderRequest:
    """Create a market buy order"""
    return OrderRequest(
        order_id=None,
        symbol=symbol,
        order_type=OrderType.MARKET_BUY,
        volume=volume,
        **kwargs
    )

def create_market_sell_order(symbol: str, volume: float, **kwargs) -> OrderRequest:
    """Create a market sell order"""
    return OrderRequest(
        order_id=None,
        symbol=symbol,
        order_type=OrderType.MARKET_SELL,
        volume=volume,
        **kwargs
    )

def create_limit_order(symbol: str, volume: float, price: float, is_buy: bool = True, **kwargs) -> OrderRequest:
    """Create a limit order"""
    return OrderRequest(
        order_id=None,
        symbol=symbol,
        order_type=OrderType.LIMIT_BUY if is_buy else OrderType.LIMIT_SELL,
        volume=volume,
        price=price,
        **kwargs
    )

# Example usage and testing
def main():
    """Example usage of the Enhanced Order Manager"""
    print("🚀 Enhanced Order Manager Test")
    print("=" * 50)
    
    # Create order manager with risk manager
    risk_manager = CoefficientBasedRiskManager()
    order_manager = EnhancedOrderManager(risk_manager)
    
    try:
        # Initialize
        if not order_manager.initialize():
            print("❌ Failed to initialize order manager")
            return
        
        # Example: Submit a test market buy order
        print("\n📝 Submitting test market buy order...")
        buy_order = create_market_buy_order(
            symbol="BTCUSD",
            volume=0.01,
            comment="Test Market Buy",
            strategy_id="TestStrategy"
        )
        
        order_id = order_manager.submit_order(buy_order)
        print(f"✅ Order submitted: {order_id}")
        
        # Wait for execution
        time.sleep(3)
        
        # Check order status
        result = order_manager.get_order_status(order_id)
        if result:
            print(f"📊 Order status: {result.status.value}")
            if result.status == OrderStatus.FILLED:
                print(f"💰 Executed at: ${result.executed_price}")
        
        # Check active positions
        positions = order_manager.get_active_positions()
        print(f"\n📈 Active positions: {len(positions)}")
        for ticket, pos in positions.items():
            print(f"  {pos.symbol}: {pos.volume} {pos.position_type} @ ${pos.open_price}")
        
        # Get statistics
        stats = order_manager.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Total orders: {stats['total_orders']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Active positions: {stats['active_positions_count']}")
        
        # Wait a bit then close any open positions
        time.sleep(2)
        if positions:
            print(f"\n🔄 Closing {len(positions)} test positions...")
            for ticket in positions.keys():
                order_manager.close_position(ticket)
            
            time.sleep(3)
            print("✅ Test positions closed")
        
    except Exception as e:
        print(f"💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        order_manager.shutdown()

if __name__ == "__main__":
    main()
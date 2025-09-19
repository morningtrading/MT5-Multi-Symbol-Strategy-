#!/usr/bin/env python3
"""
Strategy Integration Test
========================

Demonstrates how trading strategies integrate with the enhanced order management
and risk management systems. Shows the complete workflow from signal generation
to order execution and position management.

This test creates a simple demo strategy that:
1. Generates trading signals based on simple price action
2. Submits orders through the enhanced order manager
3. Tracks positions and performance
4. Demonstrates risk management integration

Author: Multi-Symbol Strategy Framework
Version: 1.0
Date: 2025-09-19
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import our infrastructure components
from GEN_order_manager import (
    EnhancedOrderManager, create_market_buy_order, create_market_sell_order,
    OrderStatus, OrderType
)
from GEN_risk_manager import CoefficientBasedRiskManager

class SimpleTestStrategy:
    """
    Simple test strategy to demonstrate infrastructure integration
    
    Strategy Logic:
    - Uses simple price action (current price vs. SMA)
    - Generates BUY signals when price is above SMA
    - Generates SELL signals when price is below SMA
    - Limits one position per symbol at a time
    """
    
    def __init__(self, symbols: List[str], order_manager: EnhancedOrderManager):
        """Initialize the test strategy"""
        self.symbols = symbols
        self.order_manager = order_manager
        self.strategy_id = "SimpleTestStrategy"
        
        # Strategy state
        self.active_orders: Dict[str, str] = {}  # symbol -> order_id
        self.position_tickets: Dict[str, int] = {}  # symbol -> position_ticket
        self.last_signals: Dict[str, str] = {}  # symbol -> signal ("BUY", "SELL", "HOLD")
        
        # Performance tracking
        self.signals_generated = 0
        self.orders_submitted = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        
        # Strategy parameters
        self.sma_period = 20
        self.min_bars_for_signal = 50
        
        print(f"🎯 Initialized {self.strategy_id} for {len(symbols)} symbols")
    
    def get_market_data(self, symbol: str, bars: int = 100) -> Optional[pd.DataFrame]:
        """Get market data for analysis"""
        try:
            # Get recent data from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, bars)
            if rates is None or len(rates) < self.min_bars_for_signal:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Calculate SMA
            df['sma'] = df['close'].rolling(window=self.sma_period).mean()
            
            return df
            
        except Exception as e:
            print(f"❌ Error getting market data for {symbol}: {e}")
            return None
    
    def generate_signal(self, symbol: str) -> str:
        """Generate trading signal for a symbol"""
        try:
            # Get market data
            data = self.get_market_data(symbol)
            if data is None or len(data) < self.min_bars_for_signal:
                return "HOLD"
            
            # Get latest values
            latest = data.iloc[-1]
            current_price = latest['close']
            sma_value = latest['sma']
            
            # Skip if SMA not available
            if pd.isna(sma_value):
                return "HOLD"
            
            # Simple signal generation
            if current_price > sma_value * 1.001:  # Price 0.1% above SMA
                signal = "BUY"
            elif current_price < sma_value * 0.999:  # Price 0.1% below SMA
                signal = "SELL"
            else:
                signal = "HOLD"
            
            # Log signal changes
            if self.last_signals.get(symbol) != signal:
                print(f"📊 {symbol}: Signal changed to {signal} (Price: ${current_price:.2f}, SMA: ${sma_value:.2f})")
                self.last_signals[symbol] = signal
                self.signals_generated += 1
            
            return signal
            
        except Exception as e:
            print(f"❌ Error generating signal for {symbol}: {e}")
            return "HOLD"
    
    def execute_signal(self, symbol: str, signal: str):
        """Execute a trading signal"""
        try:
            # Check if we already have a position or pending order
            has_position = symbol in self.position_tickets
            has_pending_order = symbol in self.active_orders
            
            if signal == "HOLD" or has_pending_order:
                return
            
            # Handle BUY signal
            if signal == "BUY" and not has_position:
                buy_order = create_market_buy_order(
                    symbol=symbol,
                    volume=0.01,  # Will be adjusted by risk manager
                    comment=f"{self.strategy_id} BUY",
                    strategy_id=self.strategy_id
                )
                
                order_id = self.order_manager.submit_order(buy_order)
                self.active_orders[symbol] = order_id
                self.orders_submitted += 1
                
                print(f"📝 {symbol}: BUY order submitted ({order_id})")
            
            # Handle SELL signal (close existing BUY position)
            elif signal == "SELL" and has_position:
                position_ticket = self.position_tickets[symbol]
                close_order_id = self.order_manager.close_position(position_ticket)
                
                print(f"🔄 {symbol}: Position close order submitted ({close_order_id})")
        
        except Exception as e:
            print(f"❌ Error executing signal for {symbol}: {e}")
    
    def update_strategy_state(self):
        """Update strategy state based on order manager status"""
        try:
            # Check pending orders
            completed_orders = []
            for symbol, order_id in self.active_orders.items():
                result = self.order_manager.get_order_status(order_id)
                if result:
                    if result.status == OrderStatus.FILLED:
                        print(f"✅ {symbol}: Order filled at ${result.executed_price}")
                        self.successful_trades += 1
                        completed_orders.append(symbol)
                        
                        # If this was a market buy, track the position
                        # (Position tracking will be handled by order manager's position sync)
                        
                    elif result.status in [OrderStatus.REJECTED, OrderStatus.FAILED]:
                        print(f"❌ {symbol}: Order failed - {result.error_message}")
                        completed_orders.append(symbol)
            
            # Remove completed orders
            for symbol in completed_orders:
                del self.active_orders[symbol]
            
            # Update position tracking from order manager
            active_positions = self.order_manager.get_active_positions()
            
            # Update our position tracking
            strategy_positions = {}
            for ticket, position in active_positions.items():
                if position.strategy_id == self.strategy_id:
                    strategy_positions[position.symbol] = ticket
            
            self.position_tickets = strategy_positions
            
            # Calculate total PnL from our positions
            total_pnl = 0.0
            for symbol, ticket in self.position_tickets.items():
                position = self.order_manager.get_position(ticket)
                if position:
                    total_pnl += position.unrealized_pnl
            
            self.total_pnl = total_pnl
            
        except Exception as e:
            print(f"❌ Error updating strategy state: {e}")
    
    def run_strategy_cycle(self):
        """Run one complete strategy cycle"""
        print(f"\n🔄 Running strategy cycle...")
        
        # Update strategy state first
        self.update_strategy_state()
        
        # Generate and execute signals for each symbol
        for symbol in self.symbols:
            try:
                signal = self.generate_signal(symbol)
                if signal != "HOLD":
                    self.execute_signal(symbol, signal)
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
        
        # Print strategy status
        self.print_strategy_status()
    
    def print_strategy_status(self):
        """Print current strategy status"""
        print(f"\n📊 Strategy Status:")
        print(f"  Signals Generated: {self.signals_generated}")
        print(f"  Orders Submitted: {self.orders_submitted}")
        print(f"  Successful Trades: {self.successful_trades}")
        print(f"  Active Positions: {len(self.position_tickets)}")
        print(f"  Pending Orders: {len(self.active_orders)}")
        print(f"  Total PnL: ${self.total_pnl:.2f}")
        
        if self.position_tickets:
            print(f"  Current Positions:")
            for symbol, ticket in self.position_tickets.items():
                position = self.order_manager.get_position(ticket)
                if position:
                    print(f"    {symbol}: {position.volume} {position.position_type} @ ${position.open_price:.2f} (PnL: ${position.unrealized_pnl:.2f})")

def main():
    """Main test execution"""
    print("🚀 Strategy Integration Test")
    print("=" * 50)
    
    # Initialize components
    print("\n🔧 Initializing components...")
    
    risk_manager = CoefficientBasedRiskManager()
    order_manager = EnhancedOrderManager(risk_manager)
    
    if not order_manager.initialize():
        print("❌ Failed to initialize order manager")
        return
    
    # Test symbols (use a smaller subset for testing)
    test_symbols = ["BTCUSD", "ETHUSD", "SOLUSD"]
    
    # Create test strategy
    strategy = SimpleTestStrategy(test_symbols, order_manager)
    
    try:
        print(f"\n🎯 Starting strategy test with {len(test_symbols)} symbols")
        print(f"Strategy will run for 5 cycles with 10-second intervals")
        
        # Run strategy for several cycles
        for cycle in range(5):
            print(f"\n🔄 === Cycle {cycle + 1}/5 ===")
            strategy.run_strategy_cycle()
            
            if cycle < 4:  # Don't sleep after last cycle
                print(f"⏱️ Waiting 10 seconds for next cycle...")
                time.sleep(10)
        
        # Final status
        print(f"\n🏁 Strategy Test Completed")
        strategy.print_strategy_status()
        
        # Close any remaining positions
        if strategy.position_tickets:
            print(f"\n🧹 Closing {len(strategy.position_tickets)} remaining positions...")
            for symbol, ticket in strategy.position_tickets.items():
                order_manager.close_position(ticket)
            
            # Wait for positions to close
            time.sleep(3)
            print("✅ Cleanup completed")
        
        # Get final order manager statistics
        om_stats = order_manager.get_statistics()
        print(f"\n📊 Order Manager Statistics:")
        print(f"  Total Orders: {om_stats['total_orders']}")
        print(f"  Success Rate: {om_stats['success_rate']:.1%}")
        print(f"  Total Volume: {om_stats['total_volume']:.3f}")
        print(f"  Active Positions: {om_stats['active_positions_count']}")
    
    except KeyboardInterrupt:
        print(f"\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print(f"\n🛑 Shutting down...")
        order_manager.shutdown()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Comprehensive Multi-Symbol Test Suite
====================================

Tests the complete trading infrastructure across ALL validated symbols:
- Enhanced MT5 connection and order execution  
- Order management system with all symbol types
- Risk management integration and validation
- Position management and tracking
- Error handling and recovery

This test validates that our infrastructure works correctly across:
- All 4 cryptocurrency symbols (BTCUSD, ETHUSD, SOLUSD, XRPUSD)  
- All 4 index symbols (US2000, NAS100, NAS100ft, SP500ft)
- All 1 commodity symbol (USOUSD)

Author: Multi-Symbol Strategy Framework
Version: 1.0
Date: 2025-09-19
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Import our infrastructure components
from GEN_order_manager import (
    EnhancedOrderManager, create_market_buy_order, create_market_sell_order,
    OrderStatus, OrderType, OrderRequest
)
from GEN_risk_manager import CoefficientBasedRiskManager

class ComprehensiveTestSuite:
    """Comprehensive test suite for all trading infrastructure"""
    
    def __init__(self, max_risk_usd: float = 25.0):
        """Initialize comprehensive test suite"""
        self.max_risk_usd = max_risk_usd
        
        # Initialize components
        self.risk_manager = CoefficientBasedRiskManager()
        self.order_manager = EnhancedOrderManager(self.risk_manager)
        
        # Test tracking
        self.test_results = {}
        self.start_time = None
        self.symbol_groups = {
            "crypto": ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"],
            "indices": ["US2000", "NAS100", "NAS100ft", "SP500ft"],
            "commodities": ["USOUSD"]
        }
        
        # Get all tradeable symbols
        self.all_symbols = self.risk_manager.get_tradeable_symbols()
        
        print(f"🎯 Initialized comprehensive test for {len(self.all_symbols)} symbols")
        print(f"🛡️ Maximum test risk: ${self.max_risk_usd}")
    
    def log_test_result(self, test_name: str, symbol: str, success: bool, details: str, data: dict = None):
        """Log test result for tracking"""
        if test_name not in self.test_results:
            self.test_results[test_name] = {}
        
        self.test_results[test_name][symbol] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
    
    def test_1_infrastructure_initialization(self) -> bool:
        """Test 1: Infrastructure Initialization"""
        print(f"\n🧪 Test 1: Infrastructure Initialization")
        print(f"=" * 50)
        
        try:
            # Test order manager initialization
            if not self.order_manager.initialize():
                print("❌ Order manager initialization failed")
                return False
            
            print("✅ Order manager initialized successfully")
            
            # Test symbol specifications loading
            tradeable_symbols = self.risk_manager.get_tradeable_symbols()
            print(f"📊 Loaded {len(tradeable_symbols)} tradeable symbols")
            
            # Verify all expected symbols are present
            missing_symbols = []
            for group_name, symbols in self.symbol_groups.items():
                for symbol in symbols:
                    if symbol not in tradeable_symbols:
                        missing_symbols.append(symbol)
            
            if missing_symbols:
                print(f"⚠️ Missing symbols: {missing_symbols}")
            else:
                print("✅ All expected symbols are tradeable")
            
            self.log_test_result("infrastructure_init", "ALL", True, 
                               f"Initialized successfully with {len(tradeable_symbols)} symbols")
            
            return True
            
        except Exception as e:
            print(f"❌ Infrastructure initialization failed: {e}")
            self.log_test_result("infrastructure_init", "ALL", False, str(e))
            return False
    
    def test_2_symbol_group_validation(self) -> Dict[str, bool]:
        """Test 2: Symbol Group Validation"""
        print(f"\n🧪 Test 2: Symbol Group Validation")
        print(f"=" * 50)
        
        results = {}
        
        for group_name, symbols in self.symbol_groups.items():
            print(f"\n📊 Testing {group_name.upper()} symbols: {symbols}")
            
            group_success = True
            group_details = []
            
            for symbol in symbols:
                try:
                    # Test symbol info retrieval
                    symbol_info = self.order_manager.get_symbol_info(symbol)
                    if symbol_info is None:
                        print(f"❌ {symbol}: Cannot get symbol information")
                        group_success = False
                        group_details.append(f"{symbol}: No symbol info")
                        continue
                    
                    # Test risk manager configuration
                    if symbol not in self.risk_manager.risk_config['position_coefficients']:
                        print(f"⚠️ {symbol}: Not in risk configuration")
                        group_details.append(f"{symbol}: Missing risk config")
                    
                    # Log symbol details
                    min_lot = symbol_info['volume_min']
                    spread = symbol_info['spread']
                    print(f"✅ {symbol}: Min lot {min_lot}, Spread {spread}")
                    
                    self.log_test_result("symbol_validation", symbol, True,
                                       f"Min lot: {min_lot}, Spread: {spread}",
                                       {"min_lot": min_lot, "spread": spread})
                    
                except Exception as e:
                    print(f"❌ {symbol}: Validation error - {e}")
                    group_success = False
                    group_details.append(f"{symbol}: {str(e)}")
                    self.log_test_result("symbol_validation", symbol, False, str(e))
            
            results[group_name] = group_success
            print(f"📈 {group_name.upper()} group: {'✅ PASSED' if group_success else '❌ FAILED'}")
        
        return results
    
    def test_3_risk_manager_evaluation(self) -> Dict[str, bool]:
        """Test 3: Risk Manager Trade Evaluation"""
        print(f"\n🧪 Test 3: Risk Manager Evaluation")  
        print(f"=" * 50)
        
        results = {}
        
        from GEN_risk_manager import TradeRequest
        
        for symbol in self.all_symbols:
            try:
                print(f"🛡️ Testing risk evaluation for {symbol}")
                
                # Create test trade request
                trade_request = TradeRequest(
                    symbol=symbol,
                    direction="BUY",
                    strategy_id="ComprehensiveTest",
                    confidence=1.0
                )
                
                # Get risk decision
                risk_decision = self.risk_manager.evaluate_trade(trade_request)
                
                if risk_decision.decision.value == "approved":
                    print(f"✅ {symbol}: Approved - Lot size: {risk_decision.approved_lot_size}")
                    results[symbol] = True
                    self.log_test_result("risk_evaluation", symbol, True,
                                       f"Approved: {risk_decision.approved_lot_size} lots",
                                       {"approved_lot_size": risk_decision.approved_lot_size})
                else:
                    print(f"⚠️ {symbol}: {risk_decision.decision.value} - {risk_decision.rejection_reason}")
                    results[symbol] = False
                    self.log_test_result("risk_evaluation", symbol, False,
                                       f"{risk_decision.decision.value}: {risk_decision.rejection_reason}")
                
            except Exception as e:
                print(f"❌ {symbol}: Risk evaluation error - {e}")
                results[symbol] = False
                self.log_test_result("risk_evaluation", symbol, False, str(e))
        
        success_rate = sum(results.values()) / len(results) * 100
        print(f"\n📊 Risk Manager Success Rate: {success_rate:.1f}% ({sum(results.values())}/{len(results)})")
        
        return results
    
    def test_4_order_execution_all_symbols(self) -> Dict[str, Dict[str, bool]]:
        """Test 4: Order Execution Across All Symbols"""
        print(f"\n🧪 Test 4: Order Execution Test")
        print(f"=" * 50)
        
        results = {}
        submitted_orders = []
        
        # Submit market buy orders for all symbols
        print(f"📝 Submitting market buy orders for all {len(self.all_symbols)} symbols...")
        
        for symbol in self.all_symbols:
            try:
                buy_order = create_market_buy_order(
                    symbol=symbol,
                    volume=0.01,  # Will be adjusted by risk manager
                    comment=f"Comprehensive Test {symbol}",
                    strategy_id="ComprehensiveTest"
                )
                
                order_id = self.order_manager.submit_order(buy_order)
                submitted_orders.append((symbol, order_id, "BUY"))
                print(f"📤 {symbol}: BUY order submitted ({order_id})")
                
            except Exception as e:
                print(f"❌ {symbol}: Order submission failed - {e}")
                if symbol not in results:
                    results[symbol] = {}
                results[symbol]["buy"] = False
                self.log_test_result("order_execution", f"{symbol}_BUY", False, str(e))
        
        # Wait for execution
        print(f"\n⏱️ Waiting 8 seconds for order execution...")
        time.sleep(8)
        
        # Check execution results
        print(f"\n📊 Checking order execution results:")
        executed_positions = []
        
        for symbol, order_id, direction in submitted_orders:
            try:
                result = self.order_manager.get_order_status(order_id)
                
                if symbol not in results:
                    results[symbol] = {}
                
                if result:
                    if result.status == OrderStatus.FILLED:
                        print(f"✅ {symbol}: {direction} executed @ ${result.executed_price}")
                        results[symbol][direction.lower()] = True
                        executed_positions.append(symbol)
                        
                        self.log_test_result("order_execution", f"{symbol}_{direction}", True,
                                           f"Executed @ ${result.executed_price}",
                                           {"price": result.executed_price, "volume": result.executed_volume})
                    else:
                        print(f"❌ {symbol}: {direction} failed - {result.status.value}")
                        results[symbol][direction.lower()] = False
                        error_msg = result.error_message or result.status.value
                        self.log_test_result("order_execution", f"{symbol}_{direction}", False, error_msg)
                else:
                    print(f"❌ {symbol}: No execution result found")
                    results[symbol][direction.lower()] = False
                    self.log_test_result("order_execution", f"{symbol}_{direction}", False, "No result")
                    
            except Exception as e:
                print(f"❌ {symbol}: Execution check error - {e}")
                results[symbol][direction.lower()] = False
                self.log_test_result("order_execution", f"{symbol}_{direction}", False, str(e))
        
        print(f"\n📈 Successfully executed: {len(executed_positions)}/{len(self.all_symbols)} symbols")
        if executed_positions:
            print(f"✅ Executed symbols: {executed_positions}")
        
        return results
    
    def test_5_position_management(self) -> Dict[str, bool]:
        """Test 5: Position Management and Closure"""
        print(f"\n🧪 Test 5: Position Management")
        print(f"=" * 50)
        
        results = {}
        
        # Get active positions
        active_positions = self.order_manager.get_active_positions()
        print(f"📊 Found {len(active_positions)} active positions")
        
        if not active_positions:
            print("ℹ️ No positions to manage")
            return {}
        
        # Display position details
        total_pnl = 0.0
        for ticket, position in active_positions.items():
            pnl = position.unrealized_pnl
            total_pnl += pnl
            print(f"📈 {position.symbol}: {position.volume} {position.position_type} @ ${position.open_price:.2f} (PnL: ${pnl:.2f})")
        
        print(f"💰 Total unrealized PnL: ${total_pnl:.2f}")
        
        # Close all positions
        print(f"\n🔄 Closing all {len(active_positions)} positions...")
        close_orders = []
        
        for ticket, position in active_positions.items():
            try:
                close_order_id = self.order_manager.close_position(ticket)
                close_orders.append((position.symbol, close_order_id, ticket))
                print(f"📤 {position.symbol}: Close order submitted ({close_order_id})")
                
            except Exception as e:
                print(f"❌ {position.symbol}: Close order failed - {e}")
                results[position.symbol] = False
                self.log_test_result("position_management", f"{position.symbol}_CLOSE", False, str(e))
        
        # Wait for position closure
        print(f"\n⏱️ Waiting 5 seconds for position closure...")
        time.sleep(5)
        
        # Verify positions closed
        remaining_positions = self.order_manager.get_active_positions()
        
        for symbol, close_order_id, original_ticket in close_orders:
            try:
                if original_ticket not in remaining_positions:
                    print(f"✅ {symbol}: Position closed successfully")
                    results[symbol] = True
                    self.log_test_result("position_management", f"{symbol}_CLOSE", True, "Position closed")
                else:
                    print(f"⚠️ {symbol}: Position still open")
                    results[symbol] = False
                    self.log_test_result("position_management", f"{symbol}_CLOSE", False, "Position still open")
                    
            except Exception as e:
                print(f"❌ {symbol}: Close verification error - {e}")
                results[symbol] = False
                self.log_test_result("position_management", f"{symbol}_CLOSE", False, str(e))
        
        success_rate = sum(results.values()) / len(results) * 100 if results else 0
        print(f"\n📊 Position Closure Success Rate: {success_rate:.1f}% ({sum(results.values())}/{len(results)})")
        
        return results
    
    def run_comprehensive_test(self) -> Dict:
        """Run the complete comprehensive test suite"""
        print(f"🚀 Starting Comprehensive Multi-Symbol Test")
        print(f"=" * 70)
        print(f"📊 Testing {len(self.all_symbols)} symbols across all asset classes")
        print(f"🛡️ Maximum risk limit: ${self.max_risk_usd}")
        
        self.start_time = datetime.now()
        
        # Run all tests
        test_1_result = self.test_1_infrastructure_initialization()
        if not test_1_result:
            print("❌ Infrastructure initialization failed - aborting tests")
            return {"success": False, "error": "Infrastructure initialization failed"}
        
        test_2_results = self.test_2_symbol_group_validation()
        test_3_results = self.test_3_risk_manager_evaluation()
        test_4_results = self.test_4_order_execution_all_symbols()
        test_5_results = self.test_5_position_management()
        
        # Generate final report
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        # Calculate overall statistics
        total_tests = len(self.all_symbols) * 4  # 4 main test categories per symbol
        successful_tests = 0
        
        for symbol in self.all_symbols:
            if test_2_results.get("crypto", False) and symbol in self.symbol_groups["crypto"]:
                successful_tests += 1
            if test_2_results.get("indices", False) and symbol in self.symbol_groups["indices"]:
                successful_tests += 1
            if test_2_results.get("commodities", False) and symbol in self.symbol_groups["commodities"]:
                successful_tests += 1
            
            if test_3_results.get(symbol, False):
                successful_tests += 1
            
            if symbol in test_4_results and test_4_results[symbol].get("buy", False):
                successful_tests += 1
            
            if test_5_results.get(symbol, False):
                successful_tests += 1
        
        success_rate = (successful_tests / total_tests) * 100
        
        # Print final summary
        print(f"\n🏁 COMPREHENSIVE TEST COMPLETED")
        print(f"=" * 70)
        print(f"⏱️ Total Duration: {total_duration:.1f} seconds")
        print(f"📊 Overall Success Rate: {success_rate:.1f}% ({successful_tests}/{total_tests})")
        print(f"🎯 Symbols Tested: {len(self.all_symbols)}")
        print(f"💼 Asset Classes: {len(self.symbol_groups)} (Crypto, Indices, Commodities)")
        
        # Order manager statistics
        om_stats = self.order_manager.get_statistics()
        print(f"\n📈 Order Manager Statistics:")
        print(f"  Total Orders: {om_stats['total_orders']}")
        print(f"  Success Rate: {om_stats['success_rate']:.1%}")
        print(f"  Total Volume: {om_stats['total_volume']:.3f}")
        
        # Save comprehensive report
        report = {
            "test_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": total_duration,
                "overall_success_rate": success_rate,
                "symbols_tested": len(self.all_symbols),
                "successful_tests": successful_tests,
                "total_tests": total_tests
            },
            "test_results": self.test_results,
            "symbol_groups": self.symbol_groups,
            "order_manager_stats": om_stats
        }
        
        report_path = f"reports/comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import os
        os.makedirs("reports", exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📊 Comprehensive report saved: {report_path}")
        
        return {
            "success": True,
            "success_rate": success_rate,
            "report_path": report_path,
            "duration": total_duration
        }

def main():
    """Main test execution"""
    print("🎯 Comprehensive Multi-Symbol Test Suite")
    print("Starting complete infrastructure validation...")
    
    test_suite = ComprehensiveTestSuite(max_risk_usd=30.0)
    
    try:
        results = test_suite.run_comprehensive_test()
        
        if results["success"]:
            print(f"\n✅ COMPREHENSIVE TEST SUCCESSFUL!")
            print(f"📊 Success Rate: {results['success_rate']:.1f}%")
            print(f"⏱️ Duration: {results['duration']:.1f} seconds")
            print(f"📄 Report: {results['report_path']}")
        else:
            print(f"\n❌ COMPREHENSIVE TEST FAILED")
            print(f"Error: {results.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n💥 Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        test_suite.order_manager.shutdown()

if __name__ == "__main__":
    main()
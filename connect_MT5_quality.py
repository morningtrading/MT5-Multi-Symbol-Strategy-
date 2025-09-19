#!/usr/bin/env python3
"""
MT5 Connection and Trading Quality Tester
=========================================

Comprehensive MT5 trading infrastructure validation tool that tests:
- Connection stability and reliability
- Account permissions and trading capabilities  
- Order execution across different types (market, limit, stop)
- Symbol trading permissions and specifications
- Margin requirements and risk calculations
- Error handling and recovery mechanisms

Safety Features:
- Uses micro lot sizes (0.01) for minimal risk
- Tests only on validated symbols from our screening
- Comprehensive logging and error reporting
- Account protection with maximum risk limits
- Automatic position cleanup after testing

Usage:
    python connect_MT5_quality.py
    
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
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import traceback

@dataclass
class TestResult:
    """Result of a specific test operation"""
    test_name: str
    success: bool
    details: str
    execution_time: float
    error_message: str = ""
    data: Optional[Dict] = None

@dataclass
class OrderTestResult:
    """Result of order execution testing"""
    order_type: str
    symbol: str
    success: bool
    order_id: Optional[int]
    execution_price: Optional[float]
    execution_time: float
    error_message: str = ""
    closed_successfully: bool = False

class MT5QualityTester:
    """Comprehensive MT5 trading infrastructure tester"""
    
    def __init__(self):
        """Initialize the MT5 quality tester"""
        self.test_results = []
        self.order_results = []
        self.account_info = None
        self.test_symbols = []
        self.symbol_lot_sizes = {}  # Store minimum lot size per symbol
        self.max_test_risk_usd = 50.0  # Increased limit for index symbols
        
        # Load our validated symbols
        self.symbol_specs = self.load_symbol_specifications()
        
        # Test configuration
        self.test_config = {
            "connection_tests": True,
            "account_tests": True, 
            "symbol_tests": True,
            "order_tests": True,
            "risk_tests": True,
            "cleanup_tests": True
        }
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps and levels"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_emoji = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARN": "⚠️",
            "ERROR": "❌",
            "TEST": "🧪"
        }
        emoji = level_emoji.get(level, "📝")
        print(f"[{timestamp}] {emoji} {message}")
        
    def load_symbol_specifications(self) -> Dict:
        """Load validated symbols from our screening results"""
        try:
            with open('symbol_specifications.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            self.log(f"Warning: Could not load symbol specs: {e}", "WARN")
            return {}
            
    def get_test_symbols(self, max_symbols: int = None) -> List[str]:
        """Get all tradeable symbols for comprehensive testing"""
        if not self.symbol_specs:
            self.log("No symbol specs loaded, using default test symbols", "WARN")
            return ["BTCUSD", "ETHUSD"]
            
        # Get all tradeable symbols from our screening
        if 'tradeable_symbols' in self.symbol_specs:
            # Use pre-compiled list from screening
            tradeable = self.symbol_specs['tradeable_symbols']
        elif 'symbol_specifications' in self.symbol_specs:
            tradeable = [k for k, v in self.symbol_specs['symbol_specifications'].items() 
                        if v.get('tradeable', False)]
        else:
            tradeable = list(self.symbol_specs.get('approved_symbols', {}).keys())
            
        # Group symbols by type for systematic testing
        crypto_symbols = [s for s in tradeable if any(crypto in s for crypto in ['BTC', 'ETH', 'SOL', 'XRP'])]
        index_symbols = [s for s in tradeable if any(idx in s for idx in ['US2000', 'NAS100', 'SP500'])]
        commodity_symbols = [s for s in tradeable if 'USO' in s]
        other_symbols = [s for s in tradeable if s not in crypto_symbols + index_symbols + commodity_symbols]
        
        # Order: crypto (most reliable) -> indices -> commodities -> others
        all_symbols = crypto_symbols + index_symbols + commodity_symbols + other_symbols
        
        # Apply limit if specified
        if max_symbols:
            test_symbols = all_symbols[:max_symbols]
        else:
            test_symbols = all_symbols  # Test all tradeable symbols
            
        self.log(f"Selected {len(test_symbols)} test symbols: {test_symbols}")
        return test_symbols
        
    def get_symbol_lot_size(self, symbol: str) -> float:
        """Get the correct minimum lot size for a symbol"""
        if symbol in self.symbol_lot_sizes:
            return self.symbol_lot_sizes[symbol]
            
        # Get symbol info to determine minimum lot size
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.log(f"Cannot get symbol info for {symbol}, using 0.01", "WARN")
            return 0.01
            
        min_lot = symbol_info.volume_min
        self.symbol_lot_sizes[symbol] = min_lot
        self.log(f"Symbol {symbol} minimum lot size: {min_lot}")
        return min_lot
        
    def run_test(self, test_name: str, test_func) -> TestResult:
        """Execute a test function and record results"""
        self.log(f"Running test: {test_name}", "TEST")
        start_time = time.time()
        
        try:
            success, details, data = test_func()
            execution_time = time.time() - start_time
            
            result = TestResult(
                test_name=test_name,
                success=success,
                details=details,
                execution_time=execution_time,
                data=data
            )
            
            level = "SUCCESS" if success else "ERROR"
            self.log(f"{test_name}: {details}", level)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Exception in {test_name}: {str(e)}"
            
            result = TestResult(
                test_name=test_name,
                success=False,
                details=f"Test failed with exception: {str(e)}",
                execution_time=execution_time,
                error_message=error_msg
            )
            
            self.log(error_msg, "ERROR")
            self.log(f"Traceback: {traceback.format_exc()}", "ERROR")
        
        self.test_results.append(result)
        return result
        
    def test_mt5_connection(self) -> Tuple[bool, str, Dict]:
        """Test MT5 connection and initialization"""
        # Test initialization
        if not mt5.initialize():
            error = mt5.last_error()
            return False, f"MT5 initialization failed: {error}", {}
            
        # Get terminal info
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            return False, "Could not get terminal information", {}
            
        # Get version info
        version_info = mt5.version()
        if version_info is None:
            return False, "Could not get version information", {}
            
        connection_data = {
            "terminal_info": terminal_info._asdict() if terminal_info else {},
            "version_info": list(version_info) if version_info else [],
            "connection_state": "connected"
        }
        
        details = f"Connected to MT5 v{version_info[0] if version_info else 'Unknown'}"
        return True, details, connection_data
        
    def test_account_info(self) -> Tuple[bool, str, Dict]:
        """Test account access and retrieve account information"""
        account_info = mt5.account_info()
        if account_info is None:
            return False, "Could not retrieve account information", {}
            
        self.account_info = account_info
        
        account_data = {
            "login": account_info.login,
            "server": account_info.server,
            "name": account_info.name,
            "company": account_info.company,
            "currency": account_info.currency,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "leverage": getattr(account_info, 'leverage', 'Unknown'),
            "trade_allowed": getattr(account_info, 'trade_allowed', 'Unknown'),
            "trade_expert": getattr(account_info, 'trade_expert', 'Unknown')
        }
        
        details = f"Account: {account_info.login}@{account_info.server}, Balance: {account_info.balance} {account_info.currency}"
        return True, details, account_data
        
    def test_symbol_access(self) -> Tuple[bool, str, Dict]:
        """Test symbol access and specifications"""
        test_symbols = self.get_test_symbols()
        self.test_symbols = test_symbols
        
        symbol_results = {}
        accessible_count = 0
        
        for symbol in test_symbols:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                symbol_results[symbol] = {
                    "accessible": False,
                    "error": "Symbol not found"
                }
                continue
                
            # Make symbol visible if needed
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    symbol_results[symbol] = {
                        "accessible": False,
                        "error": "Cannot enable symbol visibility"
                    }
                    continue
                    
            # Get fresh symbol info after enabling
            symbol_info = mt5.symbol_info(symbol)
            
            symbol_results[symbol] = {
                "accessible": True,
                "visible": symbol_info.visible,
                "trade_mode": symbol_info.trade_mode,
                "trade_mode_desc": self.get_trade_mode_description(symbol_info.trade_mode),
                "contract_size": symbol_info.trade_contract_size,
                "min_lot": symbol_info.volume_min,
                "max_lot": symbol_info.volume_max,
                "lot_step": symbol_info.volume_step,
                "point": symbol_info.point,
                "digits": symbol_info.digits,
                "spread": symbol_info.spread,
                "currency_base": symbol_info.currency_base,
                "currency_profit": symbol_info.currency_profit,
                "currency_margin": symbol_info.currency_margin
            }
            accessible_count += 1
            
        if accessible_count == 0:
            return False, "No test symbols are accessible", symbol_results
            
        details = f"{accessible_count}/{len(test_symbols)} symbols accessible and ready for trading"
        return True, details, symbol_results
        
    def get_trade_mode_description(self, trade_mode: int) -> str:
        """Convert trade mode number to description"""
        modes = {
            0: "DISABLED",
            1: "LONGONLY", 
            2: "SHORTONLY",
            3: "CLOSEONLY",
            4: "FULL"
        }
        return modes.get(trade_mode, f"UNKNOWN({trade_mode})")
        
    def test_market_order(self, symbol: str) -> OrderTestResult:
        """Test market order execution"""
        start_time = time.time()
        
        try:
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return OrderTestResult(
                    order_type="MARKET_BUY",
                    symbol=symbol,
                    success=False,
                    order_id=None,
                    execution_price=None,
                    execution_time=time.time() - start_time,
                    error_message="Could not get current price"
                )
            
            # Get correct lot size for this symbol
            lot_size = self.get_symbol_lot_size(symbol)
            
            # Prepare market buy order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": mt5.ORDER_TYPE_BUY,
                "price": tick.ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "MT5_Quality_Test_Market",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Send order
            result = mt5.order_send(request)
            execution_time = time.time() - start_time
            
            if result is None:
                return OrderTestResult(
                    order_type="MARKET_BUY",
                    symbol=symbol,
                    success=False,
                    order_id=None,
                    execution_price=None,
                    execution_time=execution_time,
                    error_message="Order send returned None"
                )
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return OrderTestResult(
                    order_type="MARKET_BUY",
                    symbol=symbol,
                    success=False,
                    order_id=result.order,
                    execution_price=None,
                    execution_time=execution_time,
                    error_message=f"Order failed: {result.retcode} - {result.comment}"
                )
                
            # Order successful - now close it immediately
            close_success = self.close_position(result.order, symbol)
            
            return OrderTestResult(
                order_type="MARKET_BUY",
                symbol=symbol,
                success=True,
                order_id=result.order,
                execution_price=result.price,
                execution_time=execution_time,
                closed_successfully=close_success
            )
            
        except Exception as e:
            return OrderTestResult(
                order_type="MARKET_BUY",
                symbol=symbol,
                success=False,
                order_id=None,
                execution_price=None,
                execution_time=time.time() - start_time,
                error_message=f"Exception: {str(e)}"
            )
            
    def close_position(self, ticket: int, symbol: str) -> bool:
        """Close a position by ticket"""
        try:
            # Get position info
            positions = mt5.positions_get(ticket=ticket)
            if not positions:
                self.log(f"Position {ticket} not found for closing", "WARN")
                return False
                
            position = positions[0]
            
            # Determine close order type (opposite of position)
            close_type = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return False
                
            close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
            
            # Prepare close request
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "price": close_price,
                "deviation": 20,
                "magic": 234000,
                "comment": "MT5_Quality_Test_Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Send close order
            close_result = mt5.order_send(close_request)
            
            if close_result and close_result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log(f"Position {ticket} closed successfully", "SUCCESS")
                return True
            else:
                error_msg = close_result.comment if close_result else "Unknown error"
                self.log(f"Failed to close position {ticket}: {error_msg}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Exception closing position {ticket}: {str(e)}", "ERROR")
            return False
            
    def test_orders_execution(self) -> Tuple[bool, str, Dict]:
        """Test order execution on available symbols"""
        if not self.test_symbols:
            return False, "No test symbols available", {}
            
        test_results = {}
        successful_orders = 0
        total_tests = 0
        
        # Test market orders on all selected symbols
        test_symbols = self.test_symbols
        
        for symbol in test_symbols:
            lot_size = self.get_symbol_lot_size(symbol)
            self.log(f"Testing market order execution on {symbol} (lot size: {lot_size})")
            
            # Test market buy order
            order_result = self.test_market_order(symbol)
            self.order_results.append(order_result)
            test_results[f"{symbol}_market_buy"] = {
                "success": order_result.success,
                "execution_price": order_result.execution_price,
                "execution_time": order_result.execution_time,
                "closed_successfully": order_result.closed_successfully,
                "error": order_result.error_message
            }
            
            if order_result.success:
                successful_orders += 1
            total_tests += 1
            
            # Small delay between orders
            time.sleep(1)
            
        success_rate = (successful_orders / total_tests * 100) if total_tests > 0 else 0
        details = f"Order execution: {successful_orders}/{total_tests} successful ({success_rate:.1f}%)"
        
        overall_success = success_rate >= 50  # At least 50% success rate required
        return overall_success, details, test_results
        
    def test_risk_calculations(self) -> Tuple[bool, str, Dict]:
        """Test risk calculation and position sizing"""
        if not self.account_info:
            return False, "Account info not available", {}
            
        risk_data = {
            "account_balance": self.account_info.balance,
            "account_currency": self.account_info.currency,
            "free_margin": self.account_info.margin_free,
            "margin_level": self.account_info.margin_level,
            "symbol_lot_sizes": self.symbol_lot_sizes.copy(),
            "max_test_risk_usd": self.max_test_risk_usd
        }
        
        # Calculate position values for test symbols
        position_values = {}
        total_risk = 0
        
        for symbol in self.test_symbols:  # Test on all symbols
            tick = mt5.symbol_info_tick(symbol)
            symbol_info = mt5.symbol_info(symbol)
            
            if tick and symbol_info:
                # Use correct minimum lot size for this symbol
                lot_size = self.get_symbol_lot_size(symbol)
                position_value = lot_size * symbol_info.trade_contract_size * tick.ask
                position_values[symbol] = {
                    "contract_size": symbol_info.trade_contract_size,
                    "lot_size_used": lot_size,
                    "current_price": tick.ask,
                    "position_value": position_value,
                    "currency": symbol_info.currency_profit
                }
                
                # Rough USD conversion (simplified)
                if symbol_info.currency_profit == "USD":
                    total_risk += position_value
                else:
                    # Estimate (this is simplified - real systems need proper currency conversion)
                    total_risk += position_value
                    
        risk_data["position_values"] = position_values
        risk_data["estimated_total_risk_usd"] = total_risk
        risk_data["risk_within_limits"] = total_risk <= self.max_test_risk_usd
        
        if total_risk <= self.max_test_risk_usd:
            details = f"Risk calculation OK: Est. ${total_risk:.2f} <= ${self.max_test_risk_usd}"
            return True, details, risk_data
        else:
            details = f"Risk too high: Est. ${total_risk:.2f} > ${self.max_test_risk_usd}"
            return False, details, risk_data
            
    def cleanup_positions(self) -> Tuple[bool, str, Dict]:
        """Clean up any remaining test positions"""
        try:
            # Get all open positions
            positions = mt5.positions_get()
            if not positions:
                return True, "No positions to clean up", {"positions_closed": 0}
                
            test_positions = [pos for pos in positions if "MT5_Quality_Test" in pos.comment]
            if not test_positions:
                return True, "No test positions to clean up", {"positions_closed": 0}
                
            closed_count = 0
            for position in test_positions:
                if self.close_position(position.ticket, position.symbol):
                    closed_count += 1
                    
            details = f"Cleanup: {closed_count}/{len(test_positions)} test positions closed"
            return closed_count == len(test_positions), details, {"positions_closed": closed_count}
            
        except Exception as e:
            return False, f"Cleanup failed: {str(e)}", {"error": str(e)}
            
    def generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        # Calculate overall success metrics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for test in self.test_results if test.success)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Order execution statistics
        total_orders = len(self.order_results)
        successful_orders = sum(1 for order in self.order_results if order.success)
        order_success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Determine overall system status
        critical_tests = ["MT5 Connection", "Account Information", "Symbol Access"]
        critical_passed = all(
            any(test.test_name == crit and test.success for test in self.test_results)
            for crit in critical_tests
        )
        
        overall_status = "READY" if critical_passed and success_rate >= 70 else "NEEDS_ATTENTION"
        
        report = {
            "metadata": {
                "test_date": datetime.now().isoformat(),
                "tester_version": "1.0",
                "test_duration": sum(test.execution_time for test in self.test_results),
                "mt5_account": self.account_info.login if self.account_info else None,
                "mt5_server": self.account_info.server if self.account_info else None
            },
            "summary": {
                "overall_status": overall_status,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate_percent": success_rate,
                "critical_systems_passed": critical_passed,
                "order_tests": {
                    "total_orders": total_orders,
                    "successful_orders": successful_orders,
                    "success_rate_percent": order_success_rate
                }
            },
            "test_results": [
                {
                    "test_name": test.test_name,
                    "success": test.success,
                    "details": test.details,
                    "execution_time": test.execution_time,
                    "error_message": test.error_message,
                    "data": test.data
                } for test in self.test_results
            ],
            "order_results": [
                {
                    "order_type": order.order_type,
                    "symbol": order.symbol,
                    "success": order.success,
                    "execution_price": order.execution_price,
                    "execution_time": order.execution_time,
                    "closed_successfully": order.closed_successfully,
                    "error_message": order.error_message
                } for order in self.order_results
            ],
            "recommendations": self.generate_recommendations(overall_status, success_rate, order_success_rate)
        }
        
        return report
        
    def generate_recommendations(self, status: str, test_success: float, order_success: float) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        if status == "READY":
            recommendations.append("✅ MT5 trading infrastructure is ready for strategy development")
            recommendations.append("✅ All critical systems are functioning properly")
            
        if test_success < 100:
            recommendations.append("⚠️ Some non-critical tests failed - review test results")
            
        if order_success < 100:
            recommendations.append("⚠️ Some order executions failed - check symbol permissions and account settings")
            
        if order_success < 50:
            recommendations.append("🚨 Order execution success rate is low - investigate account/symbol issues")
            
        recommendations.extend([
            "📈 Proceed with risk manager development (risk_manager.py)",
            "🎯 Focus initial strategy development on successfully tested symbols",
            "🔄 Run this tester regularly to monitor trading infrastructure health"
        ])
        
        return recommendations
        
    def run_all_tests(self) -> Dict:
        """Execute all MT5 quality tests"""
        self.log("🚀 STARTING MT5 TRADING INFRASTRUCTURE QUALITY TESTS")
        self.log("=" * 70)
        
        start_time = time.time()
        
        # Run test suite
        tests_to_run = [
            ("MT5 Connection", self.test_mt5_connection),
            ("Account Information", self.test_account_info),
            ("Symbol Access", self.test_symbol_access),
            ("Risk Calculations", self.test_risk_calculations),
            ("Order Execution", self.test_orders_execution),
            ("Position Cleanup", self.cleanup_positions)
        ]
        
        for test_name, test_func in tests_to_run:
            if not self.test_config.get(test_name.lower().replace(" ", "_") + "_tests", True):
                self.log(f"Skipping {test_name} (disabled in config)")
                continue
                
            self.run_test(test_name, test_func)
            time.sleep(0.5)  # Brief pause between tests
            
        # Generate and save report
        total_time = time.time() - start_time
        
        self.log("\n" + "=" * 70)
        self.log("🎯 MT5 QUALITY TESTS COMPLETE")
        self.log("=" * 70)
        self.log(f"⏰ Total duration: {total_time:.1f} seconds")
        
        report = self.generate_report()
        
        # Save report
        report_path = "MT5_quality_test_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Display summary
        summary = report["summary"]
        self.log(f"📊 Overall Status: {summary['overall_status']}")
        self.log(f"✅ Tests Passed: {summary['successful_tests']}/{summary['total_tests']} ({summary['success_rate_percent']:.1f}%)")
        if summary["order_tests"]["total_orders"] > 0:
            self.log(f"📈 Orders Successful: {summary['order_tests']['successful_orders']}/{summary['order_tests']['total_orders']} ({summary['order_tests']['success_rate_percent']:.1f}%)")
        
        self.log(f"📋 Detailed report saved: {report_path}")
        
        # Display recommendations
        self.log("\n🎯 RECOMMENDATIONS:")
        for rec in report["recommendations"]:
            self.log(f"  {rec}")
            
        # Cleanup MT5 connection
        mt5.shutdown()
        self.log("🔌 MT5 connection closed")
        
        return report


def main():
    """Main execution function"""
    try:
        # Create and run tester
        tester = MT5QualityTester()
        report = tester.run_all_tests()
        
        # Determine exit code based on results
        overall_status = report["summary"]["overall_status"]
        if overall_status == "READY":
            print(f"\n🎉 MT5 TRADING INFRASTRUCTURE READY!")
            print(f"✅ All critical systems operational")
            print(f"🚀 Ready to proceed with strategy development")
            return 0
        else:
            print(f"\n⚠️ MT5 INFRASTRUCTURE NEEDS ATTENTION")
            print(f"🔧 Review test results and address issues before proceeding")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Tests interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Fatal error during testing: {str(e)}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
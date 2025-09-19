#!/usr/bin/env python3
"""
Automated Symbol Addition Script for NewStratSIMPLE System
=========================================================

This script completely automates the addition of a new trading symbol:
1. Adds the symbol to the main list
2. Runs symbol screening
3. Updates risk configuration
4. Runs comprehensive tests
5. Validates integration

Author: NewStratSIMPLE System
Version: 1.0
Date: 2025-09-19

Prerequisites:
- MT5 must be running and connected
- Symbol must exist with your MT5 broker
- Python packages: MetaTrader5, pandas, colorama
- System files must be present
"""

import json
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Optional, Tuple
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama for Windows
except ImportError:
    # Fallback if colorama is not available
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        RESET_ALL = ""

class SymbolAdder:
    """Handles the complete process of adding a new symbol to the trading system"""
    
    def __init__(self):
        self.symbol = ""
        self.asset_class = ""
        self.coefficient = 1.0
        self.min_lot = 0.0
        self.final_min_lot = 0.0
        
        # File paths
        self.symbol_list_file = "list_symbols_capitalpoint.csv"
        self.risk_config_file = "risk_config.json"
        self.specs_file = "symbol_specifications.json"
        
        # Required files for the system
        self.required_files = [
            self.symbol_list_file,
            self.risk_config_file,
            "symbol_screener.py",
            "GEN_comprehensive_test.py"
        ]
    
    def print_colored(self, message: str, color: str = "WHITE", prefix: str = ""):
        """Print colored messages for better visibility"""
        colors = {
            "SUCCESS": Fore.GREEN,
            "ERROR": Fore.RED,
            "WARNING": Fore.YELLOW,
            "INFO": Fore.CYAN,
            "HEADER": Fore.MAGENTA,
            "WHITE": Fore.WHITE
        }
        
        color_code = colors.get(color.upper(), Fore.WHITE)
        print(f"{color_code}{prefix}{message}{Style.RESET_ALL}")
    
    def check_prerequisites(self) -> bool:
        """Verify all required files and dependencies"""
        self.print_colored("🔍 Checking prerequisites...", "HEADER")
        
        # Check required files
        for file in self.required_files:
            if not os.path.exists(file):
                self.print_colored(f"❌ Missing required file: {file}", "ERROR")
                return False
        
        # Check Python availability (should be available since we're running Python)
        try:
            import MetaTrader5 as mt5
            self.print_colored("✅ MetaTrader5 module available", "SUCCESS")
        except ImportError:
            self.print_colored("❌ MetaTrader5 module not found. Install with: pip install MetaTrader5", "ERROR")
            return False
        
        self.print_colored("✅ All prerequisites satisfied", "SUCCESS")
        return True
    
    def add_symbol_to_list(self, symbol: str) -> bool:
        """Add symbol to the main symbol list"""
        self.print_colored(f"📝 Adding {symbol} to symbol list...", "INFO")
        
        try:
            # Read current content
            with open(self.symbol_list_file, 'r') as f:
                current_content = f.read().strip()
            
            # Check if symbol already exists
            symbols = [s.strip() for s in current_content.split(',') if s.strip()]
            if symbol in symbols:
                self.print_colored(f"⚠️ Symbol {symbol} already exists in the list", "WARNING")
                return True
            
            # Add new symbol
            symbols.append(symbol)
            new_content = ','.join(symbols)
            
            # Create backup
            backup_file = f"{self.symbol_list_file}.backup"
            with open(backup_file, 'w') as f:
                f.write(current_content)
            
            # Write updated content
            with open(self.symbol_list_file, 'w') as f:
                f.write(new_content)
            
            self.print_colored(f"✅ Symbol {symbol} added to the list", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_colored(f"❌ Error adding symbol to list: {e}", "ERROR")
            return False
    
    def run_symbol_screening(self) -> bool:
        """Run the symbol screening process"""
        self.print_colored("🔍 Running symbol screening...", "INFO")
        
        try:
            # Set environment for better encoding handling
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
            
            # Run the symbol screener with encoding handling
            result = subprocess.run([sys.executable, "symbol_screener.py"], 
                                  capture_output=True, text=True, timeout=60, 
                                  env=env, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                self.print_colored("✅ Symbol screening completed successfully", "SUCCESS")
                
                # Safely get output with encoding handling
                try:
                    output = (result.stdout or "") + (result.stderr or "")
                except (TypeError, UnicodeError):
                    output = ""
                
                if f"{self.symbol}" in output and "Tradeable" in output and "Quality: 100%" in output:
                    self.print_colored(f"✅ {self.symbol} detected as tradeable (Quality: 100%)", "SUCCESS")
                    return True
                elif f"{self.symbol}" in output and "Not available" in output:
                    self.print_colored(f"❌ {self.symbol} is not available with your broker", "ERROR")
                    return False
                else:
                    self.print_colored(f"⚠️ {self.symbol} status uncertain, proceeding anyway", "WARNING")
                    return True
            else:
                # Handle stderr safely
                try:
                    stderr_msg = result.stderr or "Unknown error"
                except (TypeError, UnicodeError):
                    stderr_msg = "Encoding error in stderr"
                self.print_colored(f"❌ Symbol screening failed: {stderr_msg}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.print_colored("❌ Symbol screening timed out", "ERROR")
            return False
        except Exception as e:
            self.print_colored(f"❌ Error running symbol screening: {e}", "ERROR")
            return False
    
    def get_symbol_specifications(self, symbol: str) -> Optional[Dict]:
        """Extract symbol specifications from the generated file"""
        try:
            if not os.path.exists(self.specs_file):
                self.print_colored(f"⚠️ Specifications file not found: {self.specs_file}", "WARNING")
                return None
            
            with open(self.specs_file, 'r') as f:
                specs_data = json.load(f)
            
            symbol_specs = specs_data.get("symbol_specifications", {}).get(symbol)
            
            if symbol_specs and symbol_specs.get("available") and symbol_specs.get("tradeable"):
                return {
                    "min_lot": symbol_specs.get("min_lot", 0.01),
                    "available": symbol_specs.get("available", False),
                    "tradeable": symbol_specs.get("tradeable", False)
                }
            
            return None
            
        except Exception as e:
            self.print_colored(f"⚠️ Unable to read specifications for {symbol}: {e}", "WARNING")
            return None
    
    def update_risk_configuration(self, symbol: str, asset_class: str, 
                                coefficient: float, min_lot: float) -> bool:
        """Update the risk configuration with new symbol"""
        self.print_colored("⚙️ Updating risk configuration...", "INFO")
        
        try:
            # Read current configuration
            with open(self.risk_config_file, 'r') as f:
                risk_config = json.load(f)
            
            # Check if symbol already exists
            if symbol in risk_config.get("position_coefficients", {}):
                self.print_colored(f"⚠️ {symbol} already exists in risk configuration", "WARNING")
                return True
            
            # Add new symbol configuration
            new_symbol_config = {
                "min_lot": min_lot,
                "coefficient": coefficient,
                "asset_class": asset_class
            }
            
            if "position_coefficients" not in risk_config:
                risk_config["position_coefficients"] = {}
            
            risk_config["position_coefficients"][symbol] = new_symbol_config
            risk_config["last_updated"] = datetime.now().isoformat()
            
            # Create backup
            backup_file = f"{self.risk_config_file}.backup"
            with open(backup_file, 'w') as f:
                with open(self.risk_config_file, 'r') as orig:
                    f.write(orig.read())
            
            # Write updated configuration
            with open(self.risk_config_file, 'w') as f:
                json.dump(risk_config, f, indent=2)
            
            self.print_colored(f"✅ Risk configuration updated for {symbol}", "SUCCESS")
            return True
            
        except Exception as e:
            self.print_colored(f"❌ Error updating risk configuration: {e}", "ERROR")
            return False
    
    def run_comprehensive_test(self) -> Tuple[bool, Dict[str, bool]]:
        """Run comprehensive tests and analyze results"""
        self.print_colored("🧪 Running comprehensive tests...", "INFO")
        
        try:
            # Set environment for better encoding handling
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSSTDIO'] = '0'
            
            # Run the comprehensive test with encoding handling
            result = subprocess.run([sys.executable, "GEN_comprehensive_test.py"], 
                                  capture_output=True, text=True, timeout=120, 
                                  env=env, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0:
                self.print_colored("✅ Comprehensive tests completed", "SUCCESS")
                
                # Safely get output with encoding handling
                try:
                    output = (result.stdout or "") + (result.stderr or "")
                except (TypeError, UnicodeError):
                    output = ""
                
                test_results = {
                    "risk_approved": f"{self.symbol}" in output and "Approved" in output and "Lot size" in output,
                    "order_executed": f"{self.symbol}" in output and "BUY executed" in output,
                    "position_closed": f"{self.symbol}" in output and "Position closed successfully" in output
                }
                
                self.print_colored(f"\n📊 TEST RESULTS FOR {self.symbol}:", "HEADER")
                
                if test_results["risk_approved"]:
                    self.print_colored("✅ Risk Assessment: APPROVED", "SUCCESS")
                else:
                    self.print_colored("❌ Risk Assessment: FAILED", "ERROR")
                
                if test_results["order_executed"]:
                    self.print_colored("✅ Order Execution: SUCCESS", "SUCCESS")
                else:
                    self.print_colored("❌ Order Execution: FAILED", "ERROR")
                
                if test_results["position_closed"]:
                    self.print_colored("✅ Position Management: SUCCESS", "SUCCESS")
                else:
                    self.print_colored("❌ Position Management: FAILED", "ERROR")
                
                all_passed = all(test_results.values())
                return all_passed, test_results
                
            else:
                # Handle stderr safely
                try:
                    stderr_msg = result.stderr or "Unknown error"
                except (TypeError, UnicodeError):
                    stderr_msg = "Encoding error in stderr"
                self.print_colored(f"❌ Comprehensive tests failed: {stderr_msg}", "ERROR")
                return False, {}
                
        except subprocess.TimeoutExpired:
            self.print_colored("❌ Comprehensive tests timed out", "ERROR")
            return False, {}
        except Exception as e:
            self.print_colored(f"❌ Error running comprehensive tests: {e}", "ERROR")
            return False, {}
    
    def rollback_changes(self):
        """Rollback changes in case of failure"""
        self.print_colored("🔄 Rolling back changes...", "WARNING")
        
        try:
            # Restore symbol list backup
            backup_file = f"{self.symbol_list_file}.backup"
            if os.path.exists(backup_file):
                os.replace(backup_file, self.symbol_list_file)
                self.print_colored("✅ Symbol list restored", "SUCCESS")
            
            # Restore risk config backup
            backup_file = f"{self.risk_config_file}.backup"
            if os.path.exists(backup_file):
                os.replace(backup_file, self.risk_config_file)
                self.print_colored("✅ Risk configuration restored", "SUCCESS")
            
            self.print_colored("🔄 Rollback completed", "INFO")
            
        except Exception as e:
            self.print_colored(f"❌ Error during rollback: {e}", "ERROR")
    
    def cleanup_backups(self):
        """Clean up backup files after successful completion"""
        try:
            for backup_file in [f"{self.symbol_list_file}.backup", f"{self.risk_config_file}.backup"]:
                if os.path.exists(backup_file):
                    os.remove(backup_file)
        except Exception as e:
            self.print_colored(f"⚠️ Warning: Could not clean up backup files: {e}", "WARNING")
    
    def add_symbol(self, symbol: str, asset_class: str, 
                   coefficient: float = 1.0, min_lot: float = 0.0) -> bool:
        """Main method to add a symbol with complete workflow"""
        
        self.symbol = symbol.upper()
        self.asset_class = asset_class.lower()
        self.coefficient = coefficient
        self.min_lot = min_lot
        
        # Display header
        header = f"""
================================================================================
                    AUTOMATED SYMBOL ADDITION
================================================================================
Symbol: {self.symbol}
Asset Class: {self.asset_class}
Coefficient: {self.coefficient}
Minimum Lot: {'Auto-detection' if self.min_lot == 0 else self.min_lot}
================================================================================
"""
        self.print_colored(header, "HEADER")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            self.print_colored("❌ Prerequisites check failed. Stopping.", "ERROR")
            return False
        
        # Step 2: Add symbol to list
        if not self.add_symbol_to_list(self.symbol):
            self.print_colored("❌ Failed to add symbol to list. Stopping.", "ERROR")
            return False
        
        # Step 3: Run symbol screening
        if not self.run_symbol_screening():
            self.print_colored("❌ Symbol screening failed. Rolling back...", "ERROR")
            self.rollback_changes()
            return False
        
        # Step 4: Get symbol specifications
        specs = self.get_symbol_specifications(self.symbol)
        if specs and specs["available"] and specs["tradeable"]:
            self.final_min_lot = specs["min_lot"] if self.min_lot == 0 else self.min_lot
            self.print_colored(f"📋 Specifications detected - Min Lot: {self.final_min_lot}", "INFO")
        elif self.min_lot > 0:
            self.final_min_lot = self.min_lot
            self.print_colored(f"⚠️ Using specified MinLot: {self.final_min_lot}", "WARNING")
        else:
            self.print_colored("❌ Cannot determine MinLot. Rolling back...", "ERROR")
            self.rollback_changes()
            return False
        
        # Step 5: Update risk configuration
        if not self.update_risk_configuration(self.symbol, self.asset_class, 
                                            self.coefficient, self.final_min_lot):
            self.print_colored("❌ Failed to update risk configuration. Rolling back...", "ERROR")
            self.rollback_changes()
            return False
        
        # Step 6: Run comprehensive tests
        self.print_colored("\n🧪 TEST PHASE - This may take 15-20 seconds...", "HEADER")
        tests_passed, test_results = self.run_comprehensive_test()
        
        if tests_passed:
            # Success message
            success_message = f"""

================================================================================
                            ✅ COMPLETE SUCCESS! ✅
================================================================================
Symbol {self.symbol} has been successfully added to the system!

📊 SUMMARY:
• Symbol: {self.symbol}
• Asset Class: {self.asset_class}
• Coefficient: {self.coefficient}
• Minimum Lot: {self.final_min_lot}
• Tests: ALL PASSED

🎯 NEXT STEPS:
• Symbol is now operational
• Monitor initial performance
• Adjust coefficient if necessary

📁 MODIFIED FILES:
• {self.symbol_list_file} (backup created)
• {self.risk_config_file} (backup created)
• {self.specs_file} (regenerated)

================================================================================
"""
            self.print_colored(success_message, "SUCCESS")
            self.cleanup_backups()
            return True
        else:
            # Partial failure message
            failure_message = f"""

================================================================================
                            ❌ PARTIAL FAILURE
================================================================================
Symbol {self.symbol} was added to configuration but tests failed.

🔍 RECOMMENDED ACTIONS:
1. Verify MT5 is connected
2. Check if market is open for {self.symbol}
3. Run manually: python GEN_comprehensive_test.py
4. If problems persist, run manual rollback

🔄 MANUAL ROLLBACK IF NECESSARY:
• Remove {self.symbol} from {self.symbol_list_file}
• Remove {self.symbol} section from {self.risk_config_file}
• Re-run: python symbol_screener.py

================================================================================
"""
            self.print_colored(failure_message, "ERROR")
            return False

def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Add a new trading symbol to the NewStratSIMPLE system",
        epilog="""
Examples:
  python GEN_add_symbol.py -s XAGUSD -a precious_metal
  python GEN_add_symbol.py -s EURUSD -a forex -c 2
  python GEN_add_symbol.py -s BTCUSD -a crypto -m 0.01 -c 3
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-s', '--symbol', required=True,
                       help='Symbol name to add (e.g., XAGUSD, EURUSD, BTCUSD)')
    
    parser.add_argument('-a', '--asset-class', required=True,
                       choices=['forex', 'crypto', 'index', 'commodity', 'precious_metal'],
                       help='Asset class of the symbol')
    
    parser.add_argument('-c', '--coefficient', type=float, default=1.0,
                       help='Position coefficient (default: 1.0)')
    
    parser.add_argument('-m', '--min-lot', type=float, default=0.0,
                       help='Minimum lot size (auto-detect if 0, default: 0.0)')
    
    args = parser.parse_args()
    
    # Create adder instance and run
    adder = SymbolAdder()
    success = adder.add_symbol(args.symbol, args.asset_class, args.coefficient, args.min_lot)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
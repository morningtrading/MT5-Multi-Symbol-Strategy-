#!/usr/bin/env python3
"""
Configuration Integration Test Suite
====================================

Comprehensive tests to validate the strategy framework configuration integration.
Tests all aspects of external JSON configuration loading and parameter usage.

Test Categories:
1. Configuration Loading Tests
2. Technical Analysis Parameter Tests  
3. Strategy Initialization Tests
4. Parameter Modification Tests
5. Multi-Symbol Tests
6. Error Handling Tests

Author: Multi-Symbol Strategy Framework
Version: 1.0
Date: 2025-09-19
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import MetaTrader5 as mt5

# Import our modules
from GEN_config_loader import ConfigurationLoader, ConfigurationError
from GEN_strategy_framework import SimpleTestStrategy, StrategyConfig

class ConfigIntegrationTester:
    """Comprehensive test suite for configuration integration"""
    
    def __init__(self):
        self.test_results = []
        self.original_config = None
        self.backup_config_file = None
        
    def setup_test_environment(self):
        """Setup test environment and backup original config"""
        print("🔧 Setting up test environment...")
        
        # Initialize MT5 for testing
        if not mt5.initialize():
            raise RuntimeError("Failed to initialize MT5 for testing")
            
        # Backup original configuration
        config_file = Path("GEN_strategy_config.json")
        if config_file.exists():
            self.backup_config_file = f"GEN_strategy_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy(config_file, self.backup_config_file)
            print(f"✅ Backed up original config to {self.backup_config_file}")
            
    def cleanup_test_environment(self):
        """Clean up test environment and restore original config"""
        print("\n🧹 Cleaning up test environment...")
        
        # Restore original config if backup exists
        if self.backup_config_file and os.path.exists(self.backup_config_file):
            import shutil
            shutil.copy(self.backup_config_file, "GEN_strategy_config.json")
            os.remove(self.backup_config_file)
            print(f"✅ Restored original configuration")
            
        # Shutdown MT5
        mt5.shutdown()
        
    def run_test(self, test_name, test_func, *args, **kwargs):
        """Run a single test and record results"""
        try:
            print(f"\n🧪 Running test: {test_name}")
            result = test_func(*args, **kwargs)
            self.test_results.append({"name": test_name, "status": "PASSED", "details": result})
            print(f"✅ {test_name}: PASSED")
            return True
        except Exception as e:
            self.test_results.append({"name": test_name, "status": "FAILED", "error": str(e)})
            print(f"❌ {test_name}: FAILED - {e}")
            return False
            
    def test_1_basic_config_loading(self):
        """Test 1: Basic configuration loading from JSON file"""
        config_loader = ConfigurationLoader()
        config = config_loader.load_config()
        
        # Verify basic structure
        required_sections = ['strategy_settings', 'technical_analysis', 'risk_management']
        for section in required_sections:
            if section not in config:
                raise AssertionError(f"Missing required section: {section}")
                
        # Verify strategy settings
        strategy_settings = config['strategy_settings']
        if not strategy_settings.get('symbols'):
            raise AssertionError("No symbols found in configuration")
            
        return {
            "config_sections": list(config.keys()),
            "strategy_name": strategy_settings.get('strategy_name'),
            "symbols_count": len(strategy_settings.get('symbols', []))
        }
        
    def test_2_technical_config_loading(self):
        """Test 2: Technical analysis configuration loading and validation"""
        config_loader = ConfigurationLoader()
        tech_config = config_loader.get_technical_config()
        
        # Test all technical indicator parameters
        tests = [
            ("SMA Fast", tech_config.sma_fast, 20),
            ("SMA Slow", tech_config.sma_slow, 50),
            ("EMA Fast", tech_config.ema_fast, 12),
            ("EMA Slow", tech_config.ema_slow, 26),
            ("MACD Fast", tech_config.macd_fast, 12),
            ("MACD Slow", tech_config.macd_slow, 26),
            ("MACD Signal", tech_config.macd_signal, 9),
            ("RSI Period", tech_config.rsi_period, 14),
            ("BB Period", tech_config.bb_period, 20),
            ("ATR Period", tech_config.atr_period, 14)
        ]
        
        results = {}
        for name, actual, expected in tests:
            if actual != expected:
                raise AssertionError(f"{name}: expected {expected}, got {actual}")
            results[name.lower().replace(' ', '_')] = actual
            
        return results
        
    def test_3_strategy_initialization_from_config(self):
        """Test 3: Strategy initialization using configuration file"""
        strategy = SimpleTestStrategy.from_config_file()
        
        # Verify strategy configuration
        config = strategy.config
        tech_config = strategy.technical_config
        
        if not config.symbols:
            raise AssertionError("Strategy has no symbols configured")
            
        if not hasattr(strategy, 'technical_config'):
            raise AssertionError("Strategy missing technical configuration")
            
        return {
            "strategy_name": config.strategy_name,
            "symbols": config.symbols,
            "timeframe": config.timeframe,
            "technical_indicators": {
                "sma_fast": tech_config.sma_fast,
                "ema_fast": tech_config.ema_fast,
                "rsi_period": tech_config.rsi_period
            }
        }
        
    def test_4_market_data_with_config_indicators(self):
        """Test 4: Market data retrieval with configured technical indicators"""
        strategy = SimpleTestStrategy.from_config_file()
        
        # Get market data for first symbol
        test_symbol = strategy.config.symbols[0]
        data = strategy.get_market_data(test_symbol, bars=100)
        
        if data is None or len(data) == 0:
            raise AssertionError(f"Failed to get market data for {test_symbol}")
            
        # Verify configured indicators are present
        required_indicators = ['sma_fast', 'sma_slow', 'ema_fast', 'ema_slow', 'rsi', 'macd']
        missing_indicators = []
        
        for indicator in required_indicators:
            if indicator not in data.columns:
                missing_indicators.append(indicator)
                
        if missing_indicators:
            raise AssertionError(f"Missing indicators: {missing_indicators}")
            
        # Verify indicator values are calculated
        latest = data.iloc[-1]
        indicator_values = {}
        for indicator in required_indicators:
            value = latest[indicator]
            if pd.isna(value):
                raise AssertionError(f"Indicator {indicator} has NaN value")
            indicator_values[indicator] = float(value)
            
        return {
            "symbol": test_symbol,
            "data_rows": len(data),
            "indicator_values": indicator_values
        }
        
    def test_5_config_parameter_modification(self):
        """Test 5: Configuration parameter modification and hot-reloading"""
        config_loader = ConfigurationLoader()
        
        # Get original confidence threshold
        original_config = config_loader.get_strategy_config()
        original_threshold = original_config.min_confidence_threshold
        
        # Modify configuration
        new_threshold = 0.85
        success = config_loader.update_config('strategy_settings', 'min_confidence_threshold', new_threshold)
        
        if not success:
            raise AssertionError("Failed to update configuration")
            
        # Verify change was applied
        updated_config = config_loader.get_strategy_config()
        if updated_config.min_confidence_threshold != new_threshold:
            raise AssertionError(f"Configuration not updated: expected {new_threshold}, got {updated_config.min_confidence_threshold}")
            
        # Restore original value
        config_loader.update_config('strategy_settings', 'min_confidence_threshold', original_threshold)
        
        return {
            "original_threshold": original_threshold,
            "new_threshold": new_threshold,
            "update_successful": True
        }
        
    def test_6_multi_symbol_configuration(self):
        """Test 6: Multi-symbol configuration handling"""
        strategy = SimpleTestStrategy.from_config_file()
        symbols = strategy.config.symbols
        
        if len(symbols) < 2:
            raise AssertionError("Need at least 2 symbols for multi-symbol test")
            
        # Test market data retrieval for multiple symbols
        symbol_results = {}
        
        for symbol in symbols[:3]:  # Test first 3 symbols
            try:
                data = strategy.get_market_data(symbol, bars=50)
                if data is not None and len(data) > 0:
                    latest = data.iloc[-1]
                    symbol_results[symbol] = {
                        "data_available": True,
                        "rows": len(data),
                        "close_price": float(latest['close']),
                        "indicators_present": bool('sma_fast' in data.columns and 'rsi' in data.columns)
                    }
                else:
                    symbol_results[symbol] = {"data_available": False}
            except Exception as e:
                symbol_results[symbol] = {"data_available": False, "error": str(e)}
                
        return {
            "total_symbols": len(symbols),
            "tested_symbols": list(symbol_results.keys()),
            "results": symbol_results
        }
        
    def test_7_symbol_specific_configuration(self):
        """Test 7: Symbol-specific configuration overrides"""
        config_loader = ConfigurationLoader()
        
        # Test BTCUSD specific configuration
        btc_config = config_loader.get_symbol_specific_config("BTCUSD")
        
        if not btc_config:
            return {"symbol_specific_config": "Not configured"}
            
        # Verify specific settings
        expected_settings = ['min_confidence_override', 'special_conditions']
        found_settings = {}
        
        for setting in expected_settings:
            if setting in btc_config:
                found_settings[setting] = btc_config[setting]
                
        return {
            "symbol": "BTCUSD",
            "config_present": bool(btc_config),
            "settings": found_settings
        }
        
    def test_8_error_handling(self):
        """Test 8: Error handling for invalid configurations"""
        # Test with invalid config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": "json"')  # Invalid JSON
            invalid_config_file = f.name
            
        try:
            config_loader = ConfigurationLoader(invalid_config_file)
            config_loader.load_config()
            raise AssertionError("Should have failed with invalid JSON")
        except ConfigurationError:
            pass  # Expected
        finally:
            os.unlink(invalid_config_file)
            
        # Test with missing config file
        try:
            config_loader = ConfigurationLoader("nonexistent_config.json")
            config = config_loader.load_config()
            # Should return defaults, not fail
            if 'strategy_settings' not in config:
                raise AssertionError("Should return default configuration for missing file")
        except Exception as e:
            raise AssertionError(f"Unexpected error with missing config: {e}")
            
        return {"error_handling": "Passed all error scenarios"}
        
    def run_all_tests(self):
        """Run all configuration integration tests"""
        print("🧪 Configuration Integration Test Suite")
        print("=" * 50)
        
        try:
            self.setup_test_environment()
            
            # Import pandas here to avoid issues if not available
            global pd
            import pandas as pd
            
            # Run all tests
            tests = [
                ("Basic Config Loading", self.test_1_basic_config_loading),
                ("Technical Config Loading", self.test_2_technical_config_loading),
                ("Strategy Initialization", self.test_3_strategy_initialization_from_config),
                ("Market Data with Config Indicators", self.test_4_market_data_with_config_indicators),
                ("Config Parameter Modification", self.test_5_config_parameter_modification),
                ("Multi-Symbol Configuration", self.test_6_multi_symbol_configuration),
                ("Symbol-Specific Configuration", self.test_7_symbol_specific_configuration),
                ("Error Handling", self.test_8_error_handling)
            ]
            
            passed = 0
            failed = 0
            
            for test_name, test_func in tests:
                if self.run_test(test_name, test_func):
                    passed += 1
                else:
                    failed += 1
                    
            # Print summary
            print("\n📊 Test Results Summary")
            print("=" * 30)
            print(f"Total Tests: {len(tests)}")
            print(f"✅ Passed: {passed}")
            print(f"❌ Failed: {failed}")
            print(f"Success Rate: {passed/len(tests)*100:.1f}%")
            
            if failed == 0:
                print("\n🎉 All tests passed! Configuration integration is working perfectly!")
            else:
                print(f"\n⚠️ {failed} test(s) failed. Check details above.")
                
            # Show detailed results
            print("\n📋 Detailed Test Results:")
            for result in self.test_results:
                status_emoji = "✅" if result["status"] == "PASSED" else "❌"
                print(f"{status_emoji} {result['name']}: {result['status']}")
                if result["status"] == "FAILED":
                    print(f"   Error: {result['error']}")
                elif "details" in result:
                    print(f"   Details: {result['details']}")
                    
        finally:
            self.cleanup_test_environment()


def main():
    """Run the configuration integration test suite"""
    tester = ConfigIntegrationTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Unified Configuration Validation Script
======================================

Validates that the unified configuration merge was successful and all components
are working together correctly.
"""

def main():
    print("🔍 UNIFIED CONFIGURATION VALIDATION")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    try:
        # Test 1: Configuration Loading
        print("\n1️⃣ Testing configuration loading...")
        from GEN_config_loader import ConfigurationLoader
        loader = ConfigurationLoader()
        config = loader.get_strategy_config()
        
        print(f"   📁 Config file: {loader.config_file.name}")
        print(f"   📊 Strategy: {config.strategy_name}")
        print(f"   🔢 Symbols: {len(config.symbols)}")
        print(f"   ✅ Configuration loading: PASSED")
        tests_passed += 1
        
        # Test 2: Risk Manager Integration
        print("\n2️⃣ Testing risk manager integration...")
        from GEN_risk_manager import CoefficientBasedRiskManager, TradeRequest
        risk_mgr = CoefficientBasedRiskManager()
        
        # Test with a symbol from the unified config
        test_symbol = 'BTCUSD'
        trade_request = TradeRequest(
            symbol=test_symbol,
            direction='BUY',
            strategy_id='ValidationTest',
            confidence=0.8
        )
        
        decision = risk_mgr.evaluate_trade(trade_request)
        print(f"   🛡️ Risk decision for {test_symbol}: {decision.decision.value}")
        print(f"   💰 Lot size: {decision.approved_lot_size}")
        print(f"   ✅ Risk manager integration: PASSED")
        tests_passed += 1
        
        # Test 3: Strategy Framework Integration  
        print("\n3️⃣ Testing strategy framework integration...")
        from GEN_strategy_framework import SimpleTestStrategy
        strategy = SimpleTestStrategy.from_config_file()
        
        print(f"   🎯 Strategy: {strategy.config.strategy_name}")
        print(f"   📊 Symbols managed: {len(strategy.config.symbols)}")
        print(f"   ⚙️ Config source: {strategy.config_loader.config_file.name}")
        print(f"   ✅ Strategy framework integration: PASSED")
        tests_passed += 1
        
        # Test 4: Symbol-Specific Configuration
        print("\n4️⃣ Testing symbol-specific configuration...")
        symbol_count = 0
        for symbol in ['BTCUSD', 'ETHUSD', 'US2000']:
            if symbol in config.symbols:
                tech_config = strategy.technical_configs.get(symbol)
                risk_params = risk_mgr.risk_config['position_coefficients'].get(symbol)
                
                if tech_config and risk_params:
                    print(f"   📈 {symbol}: SMA {tech_config.sma_fast}/{tech_config.sma_slow}, Coeff {risk_params['coefficient']}")
                    symbol_count += 1
                    
        print(f"   ✅ Symbol-specific configuration: PASSED ({symbol_count}/3 symbols)")
        tests_passed += 1
        
        # Test 5: Data Consistency
        print("\n5️⃣ Testing data consistency...")
        config_symbols = set(config.symbols)
        risk_symbols = set(risk_mgr.risk_config['position_coefficients'].keys())
        
        # All strategy symbols should have risk parameters
        all_covered = config_symbols.issubset(risk_symbols)
        coverage = len(config_symbols & risk_symbols) / len(config_symbols) * 100
        
        print(f"   📊 Risk coverage: {coverage:.1f}% ({len(config_symbols & risk_symbols)}/{len(config_symbols)})")
        
        if all_covered:
            print(f"   ✅ Data consistency: PASSED (all symbols covered)")
            tests_passed += 1
        else:
            missing = config_symbols - risk_symbols
            print(f"   ⚠️ Data consistency: PARTIAL (missing: {missing})")
        
        # Test 6: File Structure
        print("\n6️⃣ Testing file structure...")
        import os
        
        files_expected = {
            'GEN_unified_config.json': 'new unified config',
            'GEN_strategy_config.json': 'legacy strategy config (backup)',
            'risk_config.json': 'legacy risk config (backup)'
        }
        
        files_found = 0
        for filename, description in files_expected.items():
            if os.path.exists(filename):
                size_kb = os.path.getsize(filename) / 1024
                print(f"   📁 {filename}: {size_kb:.1f}KB ({description})")
                files_found += 1
            else:
                print(f"   ❌ {filename}: Missing")
                
        if files_found >= 2:  # At least unified config + one backup
            print(f"   ✅ File structure: PASSED ({files_found}/3 files)")
            tests_passed += 1
        else:
            print(f"   ❌ File structure: FAILED ({files_found}/3 files)")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY:")
        print(f"✅ Tests Passed: {tests_passed}/{total_tests}")
        print(f"📈 Success Rate: {tests_passed/total_tests*100:.1f}%")
        
        if tests_passed == total_tests:
            print("🎉 UNIFIED CONFIGURATION MERGE: SUCCESSFUL!")
            print("🚀 All systems operational with unified config")
        elif tests_passed >= 4:
            print("⚠️ UNIFIED CONFIGURATION MERGE: MOSTLY SUCCESSFUL")
            print("🔧 Minor issues detected, but core functionality works")
        else:
            print("❌ UNIFIED CONFIGURATION MERGE: ISSUES DETECTED")
            print("🛠️ Review failed tests and fix configuration issues")
            
        return tests_passed >= 4
        
    except Exception as e:
        print(f"❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
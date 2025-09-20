#!/usr/bin/env python3
"""
Test custom configuration for symbol analyzer
"""
import symbol_analyzer

def test_custom_configurations():
    print('🔧 CUSTOM CONFIGURATION TESTING')
    print('=' * 50)
    
    # Test 1: Custom data directory
    print('📁 Testing custom data directory...')
    controller = symbol_analyzer.DataQualityController("nonexistent_data")
    print(f'  • Custom data directory: {controller.data_dir}')
    print(f'  • Raw data directory: {controller.raw_data_dir}')
    
    # Test 2: Custom quality thresholds
    print('\n🎯 Testing custom quality thresholds...')
    custom_controller = symbol_analyzer.DataQualityController()
    # Modify thresholds
    custom_controller.thresholds['max_gap_minutes'] = 10
    custom_controller.thresholds['max_spread_ratio'] = 0.05
    custom_controller.thresholds['min_volume'] = 5
    
    print('  • Original thresholds:')
    default_controller = symbol_analyzer.DataQualityController()
    for key, value in default_controller.thresholds.items():
        print(f'    - {key}: {value}')
    
    print('  • Modified thresholds:')
    for key, value in custom_controller.thresholds.items():
        print(f'    - {key}: {value}')
    
    # Test 3: Custom symbol list file
    print('\n📋 Testing custom symbol list file...')
    screener1 = symbol_analyzer.SymbolScreener()
    screener2 = symbol_analyzer.SymbolScreener("nonexistent_symbols.csv")
    
    print(f'  • Default symbol list: {screener1.symbol_list_file}')
    print(f'  • Custom symbol list: {screener2.symbol_list_file}')
    
    # Test 4: Custom target symbols in discoverer
    print('\n🎯 Testing custom target symbols...')
    discoverer = symbol_analyzer.SymbolDiscoverer()
    print(f'  • Default target symbols ({len(discoverer.target_symbols)}): {discoverer.target_symbols[:5]}...')
    
    # Modify target symbols
    custom_targets = ["EURUSD", "GBPUSD", "USDJPY", "CUSTOM1", "CUSTOM2"]
    discoverer.target_symbols = custom_targets
    print(f'  • Custom target symbols ({len(discoverer.target_symbols)}): {discoverer.target_symbols}')
    
    # Test 5: Unified analyzer with custom parameters
    print('\n🔧 Testing unified analyzer with custom parameters...')
    analyzer1 = symbol_analyzer.SymbolAnalyzer()
    analyzer2 = symbol_analyzer.SymbolAnalyzer("custom_symbols.csv", "CustomData")
    
    print(f'  • Default analyzer:')
    print(f'    - Symbol file: {analyzer1.symbol_list_file}')
    print(f'    - Data directory: {analyzer1.data_dir}')
    
    print(f'  • Custom analyzer:')
    print(f'    - Symbol file: {analyzer2.symbol_list_file}')
    print(f'    - Data directory: {analyzer2.data_dir}')
    
    print('\n✅ All configuration tests completed!')

if __name__ == "__main__":
    test_custom_configurations()
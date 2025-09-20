#!/usr/bin/env python3
"""
Test script for class methods and features
"""
import symbol_analyzer

def test_methods():
    print('🧪 CLASS METHODS & FEATURES TESTING')
    print('=' * 50)

    # Test SymbolScreener methods
    screener = symbol_analyzer.SymbolScreener()

    print('🔍 SymbolScreener Methods:')
    print(f'  • classify_symbol_type("BTCUSD"): {screener.classify_symbol_type("BTCUSD")}')
    print(f'  • classify_symbol_type("EURUSD"): {screener.classify_symbol_type("EURUSD")}')
    print(f'  • classify_symbol_type("XAUUSD"): {screener.classify_symbol_type("XAUUSD")}')
    print(f'  • classify_symbol_type("US500"): {screener.classify_symbol_type("US500")}')
    print(f'  • classify_symbol_type("UNKNOWN"): {screener.classify_symbol_type("UNKNOWN")}')

    # Test DataQualityController methods  
    controller = symbol_analyzer.DataQualityController()

    print('\n🔬 DataQualityController Methods:')
    print(f'  • extract_symbol_from_filename("GEN_BTCUSD_M1_1month.csv"): {controller.extract_symbol_from_filename("GEN_BTCUSD_M1_1month.csv")}')
    print(f'  • extract_symbol_from_filename("EURUSD_data.csv"): {controller.extract_symbol_from_filename("EURUSD_data.csv")}')
    print(f'  • get_grade_color("A"): {controller.get_grade_color("A")}')
    print(f'  • get_grade_color("B"): {controller.get_grade_color("B")}')
    print(f'  • get_grade_color("F"): {controller.get_grade_color("F")}')

    # Test quality scoring
    print(f'  • assign_quality_grade(95.0, 0, 0): {controller.assign_quality_grade(95.0, 0, 0)}')
    print(f'  • assign_quality_grade(85.0, 0, 1): {controller.assign_quality_grade(85.0, 0, 1)}')
    print(f'  • assign_quality_grade(65.0, 1, 0): {controller.assign_quality_grade(65.0, 1, 0)}')

    print('\n✅ All method tests completed!')

if __name__ == "__main__":
    test_methods()
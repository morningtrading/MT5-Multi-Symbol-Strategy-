#!/usr/bin/env python3
"""
Test script to analyze generated JSON reports from symbol_analyzer.py
"""
import json
import os

def analyze_reports():
    print('📊 ANALYZING GENERATED REPORTS')
    print('=' * 50)

    # Discovery analysis
    if os.path.exists('mt5_symbol_discovery.json'):
        with open('mt5_symbol_discovery.json', 'r') as f:
            discovery = json.load(f)

        print('🔍 DISCOVERY REPORT ANALYSIS:')
        print(f'  • Total MT5 symbols available: {discovery["total_available"]}')
        print(f'  • Exact matches found: {len(discovery["exact_matches"])}')
        print(f'  • Partial matches found: {len(discovery["partial_matches"])}')
        print(f'  • Popular forex pairs: {len(discovery["popular_forex"])}')
        print(f'  • Popular crypto pairs: {len(discovery["popular_crypto"])}')
        print(f'  • Popular index symbols: {len(discovery["popular_indices"])}')
        
        print('\n🎯 EXACT MATCHES:')
        for symbol in discovery["exact_matches"]:
            print(f'  ✅ {symbol}')
            
        print('\n🔍 PARTIAL MATCHES:')
        for symbol, matches in discovery["partial_matches"].items():
            print(f'  🔍 {symbol}: {matches}')

    # Symbol specifications analysis
    if os.path.exists('symbol_specifications.json'):
        with open('symbol_specifications.json', 'r') as f:
            specs = json.load(f)

        print(f'\n📋 SYMBOL SPECIFICATIONS ANALYSIS:')
        print(f'  • Total symbols screened: {specs["summary"]["total_symbols"]}')
        print(f'  • Tradeable symbols: {specs["summary"]["tradeable_count"]}')
        print(f'  • Average quality score: {specs["summary"]["avg_quality_score"]:.1f}%')
        print(f'  • Symbol groups created: {len(specs["symbol_groups"])}')

        print(f'\n🔢 SYMBOL GROUPS BREAKDOWN:')
        for group, symbols in specs['symbol_groups'].items():
            print(f'  • {group.replace("_", " ").title()}: {len(symbols)} symbols')
            print(f'    └ {", ".join(symbols)}')
            
        # Analyze spreads and trading costs
        print(f'\n💰 TRADING COST ANALYSIS:')
        spreads = {}
        for symbol, data in specs["symbol_specifications"].items():
            if data["tradeable"]:
                spreads[symbol] = {
                    'spread_points': data['spread_points'],
                    'spread_float': data['spread_float'],
                    'symbol_type': data['symbol_type']
                }
        
        # Group by symbol type
        by_type = {}
        for symbol, data in spreads.items():
            symbol_type = data['symbol_type']
            if symbol_type not in by_type:
                by_type[symbol_type] = []
            by_type[symbol_type].append((symbol, data['spread_points'], data['spread_float']))
        
        for symbol_type, symbols in by_type.items():
            avg_spread_points = sum(s[1] for s in symbols) / len(symbols)
            avg_spread_float = sum(s[2] for s in symbols) / len(symbols)
            print(f'  • {symbol_type.replace("_", " ").title()}:')
            print(f'    └ Avg spread: {avg_spread_points:.1f} points ({avg_spread_float:.5f})')
            
            # Show best and worst spreads
            symbols.sort(key=lambda x: x[1])  # Sort by spread points
            best = symbols[0]
            worst = symbols[-1]
            print(f'    └ Best: {best[0]} ({best[1]} pts)')
            print(f'    └ Worst: {worst[0]} ({worst[1]} pts)')

    # Quality analysis
    quality_file = 'CSVdata/data_quality_report.json'
    if os.path.exists(quality_file):
        with open(quality_file, 'r') as f:
            quality = json.load(f)
            
        print(f'\n🔬 DATA QUALITY ANALYSIS:')
        print(f'  • Files analyzed: {quality["summary_statistics"]["files_analyzed"]}')
        print(f'  • Total records: {quality["summary_statistics"]["total_records"]:,}')
        print(f'  • Total issues found: {quality["summary_statistics"]["total_issues"]:,}')
        print(f'  • Average quality score: {quality["summary_statistics"]["avg_quality_score"]:.1f}%')
        print(f'  • Analysis duration: {quality["summary_statistics"]["analysis_duration"]:.1f}s')
        
        # Analyze quality by symbol
        if "symbol_reports" in quality:
            grades = {}
            for symbol, report in quality["symbol_reports"].items():
                grade = report["quality_grade"]
                if grade not in grades:
                    grades[grade] = []
                grades[grade].append((symbol, report["overall_quality_score"], report["total_issues"]))
            
            print(f'\n📊 QUALITY GRADES DISTRIBUTION:')
            for grade in ['A', 'B', 'C', 'D', 'F']:
                if grade in grades:
                    symbols = grades[grade]
                    avg_score = sum(s[1] for s in symbols) / len(symbols)
                    avg_issues = sum(s[2] for s in symbols) / len(symbols)
                    print(f'  • Grade {grade}: {len(symbols)} symbols (Avg: {avg_score:.1f}%, {avg_issues:.1f} issues)')
                    for symbol, score, issues in symbols:
                        print(f'    └ {symbol}: {score:.1f}% ({issues} issues)')

if __name__ == "__main__":
    analyze_reports()
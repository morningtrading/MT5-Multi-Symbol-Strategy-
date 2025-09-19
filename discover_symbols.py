#!/usr/bin/env python3
"""
MT5 Symbol Discovery Tool
========================
Discover all available symbols in MT5 and match them against our target list.
"""

import MetaTrader5 as mt5
import pandas as pd

def discover_mt5_symbols():
    """Discover all symbols available in MT5"""
    print("🔍 MT5 SYMBOL DISCOVERY")
    print("=" * 50)
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return
    
    try:
        # Get all symbols
        all_symbols = mt5.symbols_get()
        if not all_symbols:
            print("❌ No symbols found")
            return
        
        print(f"📊 Found {len(all_symbols)} total symbols in MT5")
        
        # Our target symbols
        target_symbols = [
            "AUDUSD", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD", "NZDUSD", "SOLUSD", 
            "US2000", "US30", "US500", "USDCAD", "USDCHF", "USDCNH", "USDJPY", 
            "USDSEK", "USO.NYSE", "USTEC", "XAUUSD", "XRPUSD"
        ]
        
        print("\n🎯 SYMBOL MATCHING")
        print("-" * 50)
        
        # Find exact matches
        available_symbols = [s.name for s in all_symbols]
        exact_matches = []
        partial_matches = {}
        
        for target in target_symbols:
            if target in available_symbols:
                exact_matches.append(target)
                print(f"✅ {target:<12} - Exact match")
            else:
                # Look for partial matches
                matches = [s for s in available_symbols if target.replace('.NYSE', '') in s or s in target]
                if matches:
                    partial_matches[target] = matches
                    print(f"🔍 {target:<12} - Possible matches: {matches[:3]}")
                else:
                    print(f"❌ {target:<12} - No matches found")
        
        print(f"\n📈 SUMMARY")
        print("-" * 50)
        print(f"✅ Exact matches: {len(exact_matches)}")
        print(f"🔍 Partial matches: {len(partial_matches)}")
        print(f"❌ Not found: {len(target_symbols) - len(exact_matches) - len(partial_matches)}")
        
        if exact_matches:
            print(f"\n✅ Ready for trading: {', '.join(exact_matches)}")
        
        # Show some popular forex/crypto/index symbols available
        print(f"\n🌟 POPULAR SYMBOLS AVAILABLE:")
        print("-" * 50)
        
        forex_symbols = [s.name for s in all_symbols if any(curr in s.name for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD']) and len(s.name) == 6][:10]
        crypto_symbols = [s.name for s in all_symbols if any(crypto in s.name for crypto in ['BTC', 'ETH', 'XRP', 'SOL']) and 'USD' in s.name][:5]
        index_symbols = [s.name for s in all_symbols if any(idx in s.name for idx in ['NAS', 'SPX', 'SP500', 'DOW', 'US30', 'US500'])][:5]
        
        if forex_symbols:
            print(f"💱 Forex: {', '.join(forex_symbols)}")
        if crypto_symbols:
            print(f"₿ Crypto: {', '.join(crypto_symbols)}")
        if index_symbols:
            print(f"📊 Indices: {', '.join(index_symbols)}")
        
        # Export findings
        findings = {
            "exact_matches": exact_matches,
            "partial_matches": partial_matches,
            "popular_forex": forex_symbols,
            "popular_crypto": crypto_symbols,
            "popular_indices": index_symbols
        }
        
        with open("mt5_symbol_discovery.json", "w") as f:
            import json
            json.dump(findings, f, indent=2)
        
        print(f"\n💾 Discovery results saved to: mt5_symbol_discovery.json")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    discover_mt5_symbols()

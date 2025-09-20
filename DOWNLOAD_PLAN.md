# Missing Symbol Data Download Plan

## 📊 Overview
**Created**: 2025-09-19  
**Missing Symbols**: 12 out of 28 total symbols  
**Coverage**: Currently 57% (16/28)  
**Target**: 100% coverage (28/28)

## 🎯 Priority Levels

### 🔴 HIGH Priority (4 symbols)
**Critical for trading - Major forex pairs**
- `EURUSD` - Euro/US Dollar (most traded pair globally)
- `GBPUSD` - British Pound/US Dollar  
- `USDCHF` - US Dollar/Swiss Franc
- `USDJPY` - US Dollar/Japanese Yen

### 🟡 MEDIUM Priority (4 symbols)  
**Important for diversification**
- `XAGUSD` - Silver (precious metals exposure)
- `US30` - Dow Jones Industrial Average
- `US500` - S&P 500 Index  
- `USTEC` - NASDAQ 100 Technology
- `EURJPY` - Euro/Japanese Yen (recently added)

### 🟢 LOW Priority (4 symbols)
**Nice to have - verify availability**
- `USO.NYSE` - Oil ETF (may not be on MT5)
- `XAUUSD+` - Gold variant (check if different from XAUUSD)
- `ADAUSD` - Cardano (recently added crypto)

## 📋 Download Instructions

### Step 1: Market Hours Check
**Forex**: Available 24/5 (Sun 5PM EST - Fri 5PM EST)  
**Indices**: Market hours vary (US: 9:30AM - 4PM EST)  
**Precious Metals**: 24/5 trading  
**Crypto**: 24/7 availability  

### Step 2: Symbol Verification
Before downloading, verify symbol names in MT5:
1. Open MT5 Market Watch
2. Right-click → "Show All Symbols" 
3. Search for each symbol using alternatives from CSV
4. Note the exact symbol name used by your broker

### Step 3: Data Extraction
Run data extraction for missing symbols:
```bash
# Use your existing data extractor
python data_extractor.py --symbols-file missing_symbols_to_download.csv
```

### Step 4: Verification
After download, verify files exist:
```bash
# Check for new CSV files
ls CSVdata/raw/GEN_*_M1_1month.csv | wc -l
# Should show 28 files total (currently 16)
```

## 🔍 Potential Issues & Solutions

### Symbol Name Mismatches
- **XAGUSD** → Try: `SILVER`, `XAG/USD`, `XAGUSD.fx`
- **US30** → Try: `DJI30`, `DOW30`, `US30.fx` 
- **USO.NYSE** → May not be available (stock ETF on MT5)

### Market Availability
- Some brokers don't offer all symbols
- Precious metals might require special account types
- ETFs (USO.NYSE) rarely available on MT5

### Timing Issues  
- Download during active market hours for best results
- Forex: Best during London/NY overlap (8AM-12PM EST)
- Indices: During respective market hours

## 📈 Expected Results
After successful download:
- **Coverage**: 100% (28/28 symbols)
- **New CSV files**: 12 additional files
- **Enhanced trading**: Access to major forex pairs
- **Better diversification**: Full asset class coverage

## ⚠️ Backup Plan
If some symbols remain unavailable:
1. Check broker's symbol list
2. Consider alternative symbols (e.g., XAUUSD instead of XAUUSD+)
3. Remove unavailable symbols from trading list
4. Focus on successfully downloaded symbols

---
**Next Action**: Run data extraction during next market open (Monday 5PM EST for forex)
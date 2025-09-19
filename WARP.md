# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Development Commands

### Core System Commands
```powershell
# Test MT5 connection and trading capabilities
python connect_MT5_quality.py

# Run comprehensive configuration integration tests
python GEN_test_config_integration.py

# Test strategy framework functionality
python GEN_strategy_framework.py

# Test configuration loading system
python GEN_config_loader.py

# Extract historical data for all symbols
python data_extractor.py

# Run symbol screening and validation
python symbol_screener.py
```

### Data Quality Commands
```powershell
# Check data quality for specific symbols
python check_btc_quality.py
python check_nas100ft_quality.py
python check_usousd_quality.py
python check_xrp_quality.py

# Comprehensive data quality check
python final_quality_check.py

# Test data extraction speed
python data_extractor_old.py  # Legacy version for comparison
```

### Required Dependencies
```powershell
# Install required Python packages
pip install MetaTrader5 pandas numpy
```

## Architecture Overview

### Core Framework Architecture
This is a **multi-symbol trading strategy framework** with three main architectural layers:

1. **Configuration Layer** (`GEN_config_loader.py`)
   - External JSON configuration management
   - Symbol-specific technical analysis parameters
   - Hot-reloading of configuration changes
   - Validation and error handling

2. **Strategy Framework Layer** (`GEN_strategy_framework.py`)
   - Abstract `BaseStrategy` class for strategy development
   - Multi-symbol processing with concurrent execution
   - Real-time MT5 market data integration
   - Signal generation and processing pipeline
   - Performance metrics and trade history tracking

3. **Risk Management Layer** (`GEN_risk_manager.py`)
   - Coefficient-based position sizing system
   - Asset-class specific multipliers (crypto: 5x, indices: 1x, commodities: 1x)
   - Real-time account monitoring and protection
   - Emergency controls and exposure limits

### Symbol Management System
The framework manages **9 validated symbols across 3 asset classes**:
- **Cryptocurrencies**: BTCUSD, ETHUSD, SOLUSD, XRPUSD (min lot: 0.01)
- **Indices**: US2000, NAS100, NAS100ft, SP500ft (min lot: 0.1)
- **Commodities**: USOUSD (min lot: 0.01)

Symbol specifications are stored in `symbol_specifications.json` and loaded dynamically.

### Data Management Architecture
- **Historical Data**: 321,801+ bars across all symbols (1-minute resolution, 30-day period)
- **Data Storage**: CSV format in `CSVdata/` directory with standardized naming (`GEN_SYMBOL_M1_1month.csv`)
- **Data Quality**: Tiered system with perfect symbols (A+ grade) and natural gap symbols (B+ grade)
- **Real-time Integration**: Direct MT5 API integration for live market data

## Configuration System

### External Configuration Files
- **`GEN_strategy_config.json`**: Main strategy configuration with symbol-specific parameters
- **`risk_config.json`**: Risk management settings and coefficient definitions
- **`symbol_specifications.json`**: Symbol validation and trading permissions

### Symbol-Specific Technical Analysis
Each symbol has individually optimized parameters for all 8 technical indicators:
- SMA (Simple Moving Average) - Fast/Slow periods
- EMA (Exponential Moving Average) - Fast/Slow periods
- MACD - Fast/Slow/Signal periods
- RSI - Period and overbought/oversold levels
- Bollinger Bands - Period and standard deviation
- ATR - Period configuration
- ADX - Period and trend strength thresholds
- Volume Analysis - SMA period and spike detection

### Risk Management Configuration
- **Position Sizing**: Minimum lot × coefficient × market multiplier
- **Exposure Limits**: Max 25% total portfolio exposure, max 15% per symbol
- **Safety Limits**: 5% daily loss limit, emergency shutdown capabilities
- **Smart Filtering**: Dynamic position size reduction for high-risk symbols

## Testing Framework

### Comprehensive Test Suite (`GEN_test_config_integration.py`)
Validates all aspects of the framework:
- Configuration loading and validation
- Symbol-specific parameter application
- Technical indicator calculations
- Risk management integration
- Real-time MT5 data retrieval
- Multi-symbol processing capabilities
- Error handling and recovery

### MT5 Trading Tests (`connect_MT5_quality.py`)
Complete trading infrastructure validation:
- Connection stability and reliability
- Account permissions and capabilities
- Order execution across all symbol types
- Symbol-specific lot size handling
- Margin requirements and risk calculations
- Error handling and recovery mechanisms

### Running Tests
```powershell
# Run full test suite (recommended first step)
python GEN_test_config_integration.py

# Test MT5 trading capabilities
python connect_MT5_quality.py

# Test individual components
python GEN_config_loader.py  # Configuration system
python GEN_strategy_framework.py  # Strategy framework
```

## Development Workflow

### Strategy Development Process
1. **Inherit from BaseStrategy** class in `GEN_strategy_framework.py`
2. **Implement analyze_market()** method for signal generation
3. **Use create_signal()** method to generate trading signals
4. **Framework handles execution** via Risk Manager integration
5. **Performance tracking** is automatic

### File Naming Convention
Following user preference, all generated files use the prefix `GEN_`:
- Core files: `GEN_strategy_framework.py`, `GEN_config_loader.py`, `GEN_risk_manager.py`
- Configuration: `GEN_strategy_config.json`
- Test files: `GEN_test_config_integration.py`
- Data files: `GEN_SYMBOL_M1_1month.csv`

### MT5 Integration Requirements
- **MetaTrader 5 terminal** must be installed and running
- **Algorithmic trading** must be enabled in MT5
- **Account permissions** for all 9 validated symbols
- **Python integration** must be enabled in MT5 settings

## Data Quality System

### Symbol Quality Tiers
- **Tier 1 (Perfect)**: BTCUSD, ETHUSD, SOLUSD, XRPUSD - 100% data completeness
- **Tier 2 (Excellent)**: NAS100, NAS100ft, SP500ft, US2000, USOUSD - Natural market gaps only

### Data Validation
- **Comprehensive gap analysis** with detailed reporting
- **Spread and quality metrics** for each symbol
- **Historical coverage validation** (30-day periods)
- **Real-time data quality monitoring**

### Quality Check Commands
```powershell
# Generate comprehensive quality report
python final_quality_check.py

# Check specific symbol quality
python check_btc_quality.py
python check_xrp_quality.py
```

## Lessons Learned Implementation

### Critical Design Principles
1. **Always design for the FULL SET** - Test all symbols, not subsets
2. **Avoid hard-coded assumptions** - Use dynamic parameter retrieval from MT5
3. **Validate original requirements first** - Use complete tradeable symbol lists
4. **Implement comprehensive before optimizing** - 100% functionality before performance tuning

### Symbol-Specific Handling
- **Dynamic lot sizing**: Query MT5 for minimum lot size per symbol
- **Asset-class awareness**: Different coefficients for crypto, indices, commodities
- **Error handling**: Symbol-specific error messages and recovery mechanisms
- **Parameter validation**: Symbol-specific technical analysis parameters

## Project Status

### Completed Components
- ✅ Multi-symbol strategy framework architecture
- ✅ Symbol-specific technical analysis (8 indicators)
- ✅ External JSON configuration system
- ✅ Coefficient-based risk manager with smart filtering
- ✅ Real-time MT5 integration and testing
- ✅ Comprehensive test suite (100% success rate)
- ✅ Data extraction and quality validation system

### Next Development Phase
Focus on **MT5 Trading Infrastructure**:
1. Build production-ready order management system
2. Implement automated strategy execution
3. Create real-time monitoring dashboard
4. Develop backtesting framework
5. Add performance analytics and reporting

The framework provides a solid foundation for production trading system development with comprehensive safety controls and validation systems.
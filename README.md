# MT5 Multi-Symbol Strategy Framework

A comprehensive Python-based trading strategy framework for MetaTrader 5 with symbol-specific technical analysis, risk management, and external JSON configuration.

## 🚀 Features

### Core Components
- **Multi-Symbol Strategy Framework** - Trade multiple symbols simultaneously with individual configurations
- **Symbol-Specific Technical Analysis** - Each symbol has optimized parameters for all 8 technical indicators
- **Coefficient-Based Risk Manager** - Smart position sizing with dynamic filtering and exposure limits
- **External JSON Configuration** - All parameters externally configurable without code changes
- **Real-Time MT5 Integration** - Live market data and trade execution

### Technical Indicators (8 Total)
1. **SMA (Simple Moving Average)** - Fast/Slow periods per symbol
2. **EMA (Exponential Moving Average)** - Fast/Slow periods per symbol  
3. **MACD** - Fast/Slow/Signal periods per symbol
4. **RSI (Relative Strength Index)** - Period and overbought/oversold levels per symbol
5. **Bollinger Bands** - Period and standard deviation multiplier per symbol
6. **ATR (Average True Range)** - Period per symbol
7. **ADX (Average Directional Index)** - Period and trend strength thresholds per symbol
8. **Volume Analysis** - SMA period and spike detection per symbol

### Supported Symbols
- **Cryptocurrencies**: BTCUSD, ETHUSD, SOLUSD, XRPUSD
- **Indices**: US2000, NAS100, NAS100ft, SP500ft  
- **Commodities**: USOUSD (Oil)

## 📁 Project Structure

```
MT5-Multi-Symbol-Strategy/
├── GEN_strategy_framework.py      # Main strategy framework with symbol-specific TA
├── GEN_config_loader.py           # Configuration management system
├── GEN_strategy_config.json       # External strategy configuration
├── GEN_risk_manager.py            # Coefficient-based risk management
├── GEN_test_config_integration.py # Comprehensive test suite
├── connect_MT5_quality.py         # MT5 connection and trade quality tester
├── symbol_screener.py             # Symbol discovery and screening
├── data_extractor.py             # Historical data extraction
└── risk_config.json              # Risk management configuration
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MetaTrader 5 terminal installed
- MT5 account with trading permissions

### Required Libraries
```bash
pip install MetaTrader5 pandas numpy
```

### MT5 Setup
1. Install and login to MetaTrader 5
2. Enable algorithmic trading
3. Add symbols to Market Watch
4. Ensure Python integration is enabled

## 🚦 Quick Start

### 1. Test MT5 Connection
```bash
python connect_MT5_quality.py
```

### 2. Run Symbol-Specific Configuration Test
```bash
python GEN_config_loader.py
```

### 3. Test Strategy Framework
```bash
python GEN_strategy_framework.py
```

### 4. Run Comprehensive Tests
```bash
python GEN_test_config_integration.py
```

## ⚙️ Configuration

### Symbol-Specific Parameters
Each symbol has unique technical analysis parameters in `GEN_strategy_config.json`:

```json
{
  "symbol_specific": {
    "BTCUSD": {
      "technical_analysis": {
        "sma_fast": 5, "sma_slow": 15,
        "ema_fast": 8, "ema_slow": 21,
        "macd_fast": 8, "macd_slow": 17, "macd_signal": 6,
        "rsi_period": 10, "rsi_overbought": 75, "rsi_oversold": 25,
        "adx_period": 12, "adx_strong_trend": 30, "adx_very_strong_trend": 50,
        "bb_period": 15, "bb_std_dev": 2.2,
        "atr_period": 10,
        "volume_sma_period": 15, "volume_spike_multiplier": 2.5
      }
    }
  }
}
```

### Risk Management
- **Smart Dynamic Filtering**: Automatically reduces position sizes for high-risk symbols
- **Exposure Limits**: Maximum 25% total portfolio exposure
- **BTCUSD Coefficient Cap**: Capped at 1.0 for safety
- **Market Condition Multipliers**: Bull/bear/volatility adjustments

## 📊 Architecture Overview

### Strategy Flow
1. **Configuration Loading** - Load symbol-specific parameters from JSON
2. **Market Data Retrieval** - Get real-time data from MT5
3. **Technical Analysis** - Calculate 8 indicators per symbol using custom parameters
4. **Signal Generation** - Generate trading signals based on technical conditions
5. **Risk Management** - Evaluate position sizes and exposure limits
6. **Trade Execution** - Execute approved trades through MT5

### Symbol-Specific Design
- **Individual Parameter Sets**: Each symbol has optimized technical analysis parameters
- **Asset-Class Specialization**: Crypto, indices, and commodities use different configurations
- **Optimization-Ready**: Perfect foundation for backtesting and parameter optimization

## 🧪 Testing

### Comprehensive Test Suite
The project includes a full test suite validating:
- ✅ Configuration loading and validation
- ✅ Symbol-specific parameter application
- ✅ Technical indicator calculations
- ✅ Risk management integration
- ✅ Real-time MT5 data retrieval
- ✅ Multi-symbol processing
- ✅ Error handling and recovery

### Test Results
Latest test run: **100% Success Rate** (8/8 tests passed)

## 🎯 Current Status

### ✅ Completed
- Multi-symbol strategy framework architecture
- Symbol-specific technical analysis (8 indicators)
- External JSON configuration system
- Coefficient-based risk manager with smart filtering
- Real-time MT5 integration and testing
- Comprehensive test suite

### 🚧 Next Steps
- Parameter optimization through backtesting
- Historical data analysis and strategy validation
- Advanced signal generation algorithms
- Performance tracking and analytics
- Automated parameter tuning system

## 📈 Performance Features

### Risk Management
- **Portfolio Exposure**: Max 25% total exposure
- **Individual Position**: Max 15% per symbol
- **Daily Loss Limit**: 5% maximum daily loss
- **Smart Position Sizing**: Minimum lot × coefficient × market multiplier

### Technical Analysis
- **Symbol-Optimized**: Each symbol uses parameters optimized for its characteristics
- **Multi-Timeframe Ready**: Framework supports multiple timeframe analysis
- **Real-Time Calculations**: All indicators calculated in real-time from live data

## 🤝 Contributing

This is a comprehensive trading framework designed for:
- Strategy developers wanting symbol-specific optimization
- Quantitative traders needing robust risk management
- Algorithmic trading with external parameter control
- Multi-asset portfolio trading strategies

## ⚠️ Disclaimer

This trading framework is for educational and research purposes. Trading involves significant financial risk. Always test thoroughly with paper trading before live implementation.

## 📧 Contact

For questions about implementation, optimization, or strategy development, refer to the comprehensive documentation and test results included in this repository.

---

**Built with Python 3.13 | MetaTrader 5 | Real-Time Market Data**
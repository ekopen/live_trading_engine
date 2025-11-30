# ML Trading Strategies  

This is part of my overarching **Live Trading Platform** project. Visit [www.erickopen.com](http://www.erickopen.com) to view comprehensive documentation.  

## Overview  
Continuously trains an array of machine learning models on recent market data, records their performance, and uploads the updated models to an AWS repository.

## Details  
- Accesses minute-aggregated data from the **Market Data Storage** module and retrains multiple ML models at frequent intervals (ranging from every 4 to 24 hours) using the most recent seven days of pricing ticks.  
- After training, each model’s performance metrics are logged in and the model is saved.
- The **Systematic Trading** module then retrieves models and uses them to generate signals for live trading decisions.  

## Future Improvements  
- Expand performance tracking with more detailed backtesting and financial evaluation metrics.  
- Broaden training beyond Ethereum to include all supported cryptocurrencies for multi-asset strategies.  
- Migrate model documentation to JSON files so updates don’t require rerunning Python scripts.  

## Known Issues   
- Models can occasionally develop runaway biases (favoring persistent buy/sell signals) or hold positions indefinitely. Implement additional training logic to promote balanced decision-making.  


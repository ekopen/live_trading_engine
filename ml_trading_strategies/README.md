# ML Trading Strategies  

This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Continuously trains an array of machine learning models on recent market data, records their performance, and uploads the updated models to an AWS repository.

## Details  
- Accesses minute-aggregated data from the **Market Data Storage** module and retrains multiple ML models at frequent intervals (ranging from every 4 to 24 hours) using the most recent seven days of pricing ticks.  
- After training, each model’s performance metrics are logged in **ClickHouse**, and the model itself is uploaded to **AWS**.  
- The **Systematic Trading** module then retrieves models from this AWS repository to make live trading decisions.  

## Future Improvements  
- Expand performance tracking with more detailed backtesting and financial evaluation metrics.  
- Broaden training beyond Ethereum to include all supported cryptocurrencies for multi-asset strategies.  
- Implement a notification system that pings the **Systematic Trading** module whenever a new model is trained.  
- Migrate model documentation to JSON files so updates don’t require rerunning Python scripts.  

## Known Issues   
- Models can occasionally develop runaway biases (favoring persistent buy/sell signals) or hold positions indefinitely. Implement additional training logic to promote balanced decision-making.  

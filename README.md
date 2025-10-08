# Live Trading Engine 
Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
This is the repo for a trading engine that is designed to be up 24/7. It continuously intakes market data, stores that data, uses the data to frequently train machine learning models, and then uses those machine learning models to make trading decisions. This project showcases my skillset in creating trading infrastructure.

## Details
- This project consists of 4 modules:
    - Market Data Stream: streams real time tick level market data for five different cryptocurrencies
    - Market Data Storage: continuously populates a database with new tick data
    - ML Trading Strategies: frequently retrains machine learning models based on new market data
    - Systematic Trading: uses ml models to simulate making trading decisions, incorporating an execution, risk assessment, and portfolio tracking engine
- This code is containerized via Docker and currently runs on a Digial Ocean server. Dashboards (available on my website) are created via Grafana.

## Future Improvements
- Introduce Kubernetes for automatic resource scaling.
- Create one config file for all modules, as well as JSON files for different ML models/strategies.
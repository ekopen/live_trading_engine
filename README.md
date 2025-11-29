# Live Trading Engine  

Visit [www.erickopen.com](http://www.erickopen.com) to view comprehensive documentation.  

## Overview  
This repository contains a fully automated trading engine designed to operate 24/7. It continuously ingests market data, stores that data, retrains machine learning models on a frequent basis, and uses those models to make trading decisions. This project highlights my ability to design and implement robust trading infrastructure.

## Details  
This project consists of four primary modules:  
- **Market Data Stream:** Streams real-time, tick-level market data for five different cryptocurrencies.  
- **Market Data Storage:** Continuously populates a database with incoming tick data.  
- **ML Trading Strategies (Machine Learning Service):** Retrains machine learning models frequently based on the latest market data.  
- **Systematic Trading (Execution Engine):** Simulates real-time trading decisions using ML models, with integrated execution, risk management, and portfolio tracking components.  

The system is containerized using Docker and deployed on a DigitalOcean server. Dashboards (available on my website) are built using Grafana for real-time monitoring and visualization.  

## Future Improvements  
- Implement Kubernetes for automatic resource scaling and orchestration.
- Expand the portfolio tracking module.
- Consolidate configuration into a single master config file, with modular JSON files defining various ML models and trading strategies. This wil help turn them on/off.
- Add unit tests.
- Add Grafana alerts for module health.

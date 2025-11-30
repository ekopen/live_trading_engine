# Market Data Stream  

This is part of my overarching **Live Trading Platform** project. Visit [www.erickopen.com](http://www.erickopen.com) to view comprehensive documentation.  

## Overview  
Configures a Kafka producer that captures real-time market data from a WebSocket. The producer publishes data to a Kafka topic, which downstream consumers use to update market data tables and retrieve live prices.  

## Details  
- Connects to a **Finnhub WebSocket** that streams tick-level cryptocurrency pricing data from **Binance** for multiple currencies.  
- Data retention is capped by both time duration and memory size to optimize storage and minimize latency, configured through **Kafka retention policies**.  
- Other modules in the **Live Trading Engine** subscribe to this Kafka topic:  
  - The **Market Data Storage** module continuously writes streaming data into **ClickHouse** for historical analysis.  
  - The **Systematic Trading** module consumes the latest prices for trade execution.  

## Future Improvements  
- Expand the producer to include bid/ask price levels for higher-frequency trading strategies.  
- Implement Kafka partitioning and schema management to improve scalability as data volume increases.  

## Known Issues  
- Reconfigure Docker so dependent services shut down gracefully if the stream becomes unavailable.  


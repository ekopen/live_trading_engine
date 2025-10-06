# Market Data Stream  
This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Configures a Kafka producer that captures real-time market data from a websocket. The producer publishes data to a Kafka topic, which downstream consumers use to update market data tables and retrieve live prices.  

## Details  
- Connects to a Finnhub websocket that streams crypto pricing data (tick level granularity) from Binance for multiple currencies.  
- Retention is capped by both time duration and memory size to optimize storage and keep latency low (configured via Kafka retention policies).  
- Integrated with Prometheus and Grafana to track message throughput, producer health, memory usage, and server metrics.  
- Other modules in the Live Trading Engine subscribe to this Kafka topic. For example, the market_data continuously writes streaming data into ClickHouse for historical analysis, while the trading consumes the latest prices for use in trading strategy execution.

## Future Improvements  
- Expand the producer include bid/ask price levels (for higher frequency strategies).   
- Explore partitioning and schema management for scalability as data volume grows.  

## Known Issues  
- Configuration files may contain redundant or overly complex settings. 

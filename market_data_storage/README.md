# Market Data Storage  
This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Captures market data from a Kafka consumer and stores it in a ClickHouse database, eventually archiving old data to AWS. Downstream applications use this data to generate trading algorithims.

## Details
- Creates a Kafka consumer that subscribes to a topic generated in the Market Data Stream module, featuring market tick data of multiple currencies.
- Continuously writes new data from the consumer to a ClickHouse database using batch methodology. A downsampled minute level tick table is additionally automatically generated.
- Retention in Clickhouse is capped by a 7 day time limit. Data older than 7 days is frequently archived to a parquet, removed from Clickhouse, uploaded to AWS, and then deleted off local drives.
- Metrics such as data ingestion rate, processing lag, and websocket lag are frequently recorded into Clickhouse.
- The downsampled market data generated in this module is used to train algorithims in the ML Trading Strategies module and serve as feature data for the Systematic Trading module.

## Future Improvements  
- Switch from Clickhouse batch insert to Clickhouse Kafka engine.

## Known Issues  
- N/A
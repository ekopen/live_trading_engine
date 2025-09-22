# Market Data Storage  
This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Captures market data from a Kafka consumer (along with ingestion metrics) and stores it in a ClickHouse database, eventually archiving old data to AWS. Downstream applications use this data to generate trading algorithims.

## Details
- Creates a Kafka consumer that subscribes to a topic generated in the market_data_stream module, featuring market tick data of multiple currencies.
- Continuously writes new data from the consumer to a ClickHouse database using batch methodology.
- Retention in Clickhouse is capped by a time limit for memory and performance optimization. Old data is frequently archived to a parquet and then uploaded to AWS, and then is deleted off local drives and removed from ClickHouse.
- Metrics such as message ingestion rate, Kafka lag, and websocket lag are frequently recorded and populated in other ClickHouse tables, which are subject to the same archiving process.
- The market data saved in this Clickhouse table is used downstream in other modules, where it is querired to generate logic for algorithims in the trading module.

## Future Improvements  
- Switch from Clickhouse batch insert to Clickhouse Kafka engine.
- Revisit crash logic, which may not be as necessary now that this is decoupled from Kafka.
- Create seperate container for clickhouse deletion/creation/alteration, which can be ran one time.
- Turn on cloud migration with cost tracking.

## Known Issues  
- Parquets may not be written right now, fix os directory details in cloud migration.
- AWS upload is turned off for price considerations.

# Systematic Trading 
This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Continuosly runs trading algorithims, records execution activity, and monitors portfolio performance. This utilizes both live market data from the market_data_stream module and historical data from the market_data_storage module.

## Details
- Portfolios for each strategies are initialized using a predetermined allocation of cash.
- Simple trading strategies are represented algorithimically and implemented via standardized class structure in Python.
- The trading algorithims intake current prices from the market_data_stream module, are routinely retrained on historical data from market_data_storage, and use other arbitrary rules to frequently generate signals.
- Once a signal is generated, the trade is evaluated by risk engines, which may approve and disapprove of an order.
- If approved, the trade is moved to the execution engine, which fills the order using simulated delay/slippage conditions.
- ClickHouse is used to create tables related to the portfolio, which are then visualized via Grafana. These include an up to date current state table for each strategy, a time series that shows snapshots of each strategy over time, and recorded execution data.


## Future Improvements
**Planned Features:**
- Better orchestrate all the strategies. They should be individually turned on and off.
- Start tracking PNL metrics, risk metrics, etc, and have those be part of the risk consideration.
- Implement slippage conditions. Additionally, this model only supports limit orders, which messes with long only strategies.
- Have model refreshes triggered by pings, not on a timed schedule.
- Finalizing shut down logic/initialization logic, such as having a cash portfolio that gets divvyed up at the start

**Known Issues:**
- The Kafka consumer may be inefficient right now, and should be looked into.
- Shut down is not clean, the process needs to be fixed for errors.

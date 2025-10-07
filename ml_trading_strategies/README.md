# ML Trading Strategies 
This is part of my overarching **Live Trading Engine** project. Visit [www.erickopen.com](http://www.erickopen.com) to see my projects running live and to view comprehensive documentation.  

## Overview  
Continously trains an array of machine learning models on recent market data, records their performance. and uploads the new models to an AWS repository.

## Details
- Accessing minute aggregated data from the Market Data Storage module, a variety of ML models are retrained on frequent intervals (ranging from every 4 to 24 hours) using the most recent 7 days of pricing ticks.
- Once they are trained, each modules performance is recorded in Clickhouse, and then the model itself is uploaded to AWS.
- The Systematic Trading module accesses the AWS repository these models are uploaded to, where they are implemented to make live trading decisions.

## Future Improvements
- While some metrics each models performance is recorded, there could be more detailed backtesting results to describe the models performance from a financial point of view.
- This currently just creates ML models based on Ethereum data. Ideally, training should intake all currencies to create multi-assets strategies.
- Send pings to the Systematic Trading module every time a model is trained.
- Move documentation of models to a JSON file, so they are not wrapped up in Pyhton code that needs to be reran to update.
 
**Known Issues:**
- The LTSM training may have issues because it only features a 2D dataset.
- Models are prone to having a runaway bias (either in buying or selling) or holding infinitely long. Look into training models to return balanced decisions.

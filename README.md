Recommender Module: <br>

- crawler.py: A crawler library which is capable of crawling address and token transaction data
- address_crawler.py: Calling the crawler module to crawl transaction data by address.
- token_crawler.py: Calling the crawler module to crawl transaction data by token.
- preprocess.py: Prepare address transaction data into the form needed for recommender
- recommend.py: Main recommend function

Trend Prediction Module:

- price_crawler: Use CoinGecko API to retrieve hourly price data for token
- price_crawler_minute.py: Use archive minute data, same API as price crawler
- trend.py: Hyper-parameter tuning script for hourly data
- trend_minute.py Hyper-parameter tuning script for minute data
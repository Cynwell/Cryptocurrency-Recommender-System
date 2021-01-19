# Cryptocurrency Recommender System
## **Project Description**
A project that utilizes cryptocurrency transaction network and cryptocurrency prices to give personalized recommendations to cryptocurrency investors.

This project consists of a front-end module to show personalized recommendations to investors and two back-end modules to compute recommendations, namely **The Recommender System Module** and **The Trend Prediction Module**.

---
## **Back-end Modules Description**

## 1. Recommender System Module
- crawler.py: A crawler library which is capable of crawling address and token transaction data
- address_crawler.py: Calling the crawler module to crawl transaction data by address.
- token_crawler.py: Calling the crawler module to crawl transaction data by token.
- preprocess.py: Prepare address transaction data into the form needed for recommender
- recommend.py: Main recommend function

## 2. Trend Prediction Module
- price_crawler: Retrieving hourly token price data from CoinGecko
- price_crawler_minute.py: Retrieving archived minute resolution data from Kaggle (https://www.kaggle.com/tencars/392-crypto-currency-pairs-at-minute-resolution)
- trend.py: Hyper-parameter tuning script for **hourly** data source
- trend_minute.py: Hyper-parameter tuning script for **minute** resolution data source
- trend_minute_multi_CPU.py: Hyper-parameter tuning script for minute resolution data source, with the support of **multi-processing** to speed up finetuning process
- backtrader-strategy.ipynb: Backtesting models that we have selected in backtrader and measuring strategies in differentk metrics
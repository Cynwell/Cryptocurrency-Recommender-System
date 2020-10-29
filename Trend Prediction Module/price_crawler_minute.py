import os
from copy import copy
import pandas as pd
import talib
from talib import abstract
import numpy as np


def retrieve_data(target_filename=None, root='price_data/archive/'):
    '''
    Retrieve data from the root directory as specified. This function is intended for the minute resolution dataset downloaded from Kaggle only (https://www.kaggle.com/tencars/392-crypto-currency-pairs-at-minute-resolution).
    Input:
		target_filename <str>: Defaults to None, meaning that it will extract all csv data in the directory. If specified, it will only extract that one specific file only. The target filename should include '.csv' too in the input.
        root <str>: Represents the directory where the price data is being stored.
    Output:
        price_data_dict <dict>: A dictionary where keys are the filename or trading pairs, and values are the corresponding price data in pd.DataFrame format. DataFrame index is [date], columns are [open, close, high, low, volume].
    '''
    if target_filename is None:
        price_data_dict = {}
        for f in os.listdir(root):
            if f.endswith('.csv'):
                df = pd.read_csv(root + f, usecols=['time', 'open', 'close', 'high', 'low', 'volume'])
                df['date'] = pd.to_datetime(df['time'], unit='ms')
                df.drop(columns=['time'], inplace=True)
                df = df.set_index('date')
                price_data_dict[f[:-4]] = df
        return price_data_dict
    else:
        df = pd.read_csv(root+target_filename, usecols=['time', 'open', 'close', 'high', 'low', 'volume'])
        df['date'] = pd.to_datetime(df['time'], unit='ms')
        df.drop(columns=['time'], inplace=True)
        df = df.set_index('date')
        return df


def build_ta_features(df, freq='1D', ta_list=None):
    '''
    To build OHLCV (Open High Low Close Volume) features, and advanced features provided by TA-Lib.
    Input:
        df <pd.DataFrame>: A DataFrame object that contains columns ['timestamp', 'prices', 'market_caps', 'total_volumes']. It should be retreived from CoinGecko.
        freq <str>: A string that specifies the frequency of sampling. For different frequency notations, check https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases.
        ta_list <list>: A list of techical analysis features to be built. For the whole list of feature names, check TA-Lib website: https://mrjbq7.github.io/ta-lib/funcs.html.
                             If None, it will build all features available in TA-Lib. Otherwise, it will only build features as specified in the feature_list.
    Return:
        df <pd.DataFrame>: A DataFrame object where each column represents a unique feature (with name), and each row represents a sampled timestamp (with time).
    '''
    df = df.copy()

    # First fill missing close price of the resampled df with previous close price
    df = pd.concat([df.resample(freq)['open'].agg('first'),
                    df.resample(freq)['high'].agg('max'),
                    df.resample(freq)['low'].agg('min'), 
                    df.resample(freq)['close'].agg('last').ffill(),
                    df.resample(freq)['volume'].agg('sum').fillna(0.0)], axis=1)
    # Then fill missing open high low price of the resampled df with the previous close price (copied to the same row)
    df = pd.concat([df['open'].fillna(df['close']),
                    df['high'].fillna(df['close']),
                    df['low'].fillna(df['close']),
                    df['close'],
                    df['volume']], axis=1)

    # Building advanced features using TA-Lib
    # For MAVP, it allows moving average with variable periods specified, we'll just skip this function.
    if ta_list is None:
        ta_list = talib.get_functions()
    for i, x in enumerate(ta_list):
        try:
            output = eval('abstract.' + x + '(df)')
            output.name = x.lower() if type(output) == pd.core.series.Series else None
            df = pd.merge(df, pd.DataFrame(output), left_on = df.index, right_on = output.index)
            df = df.set_index('key_0')
        except:
            pass
    df.index.names = ['date']
    return df


def build_features(df, freq='1D', ta_list=None, ys={'1D-price': 2, '3D-price': 6}, roll=3):

    '''
    To build features for the inputted df by appending newly built features to the df.
    Input:
        df <pd.DataFrame>: A pd.DataFrame object which inlude [date] as index, and [open, close, high, low, volume] in columns.

    '''
    df = build_ta_features(df, freq=freq, ta_list=ta_list)
    # Add rolling features
    columns = copy(df.columns)
    for i in range(roll):
        for c in columns:
            df[c + '-r' + str(i + 1)] = df[c].shift(i + 1)
    # Add labels
    for target_name, period in ys.items():
        df[target_name] = (df['close'].shift(-period) - df['close']) > 0
    df = df.replace(np.inf, np.nan).dropna(how='all', axis=1).dropna(how='any', axis=0)
    return df


if __name__ == '__main__':
    # First go to https://www.kaggle.com/tencars/392-crypto-currency-pairs-at-minute-resolution to download data zip file first
    # Unzip the file, put the folder called 'archive' under the 'price_data' directory
    root = 'price_data/archive/'
    price_data_dict = retrieve_data(root=root)

    for key in price_data_dict.keys():
        df = build_features(price_data_dict[key], freq='12H', ta_list=['ROC', 'MOM', 'EMA'])
        print(df.head())
        break
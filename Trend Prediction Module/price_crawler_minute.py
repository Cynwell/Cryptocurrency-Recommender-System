import os
from copy import copy
import pandas as pd
import talib
from talib import abstract
import numpy as np
import re


def get_period_and_frequency(string):
    '''
    Get period and frequency from a string. Eg: '3min' -> (3, 'min'); '7D' -> (7, 'D'), and then outputs are passed into the pd.DataFrame.shift().
    Input:
        string <str>: A string that contains information about the period and the frequency.
    Return:
        period <int>: An integer indicating the period length specified in string.
        freq <str>: A string indicating the frequency specified in string.
    '''
    period = None
    freq = None
    try:
        period = int(re.search('^[0-9]+', string).group())
        freq = re.search('[A-z]+$', string).group()
    except:
        raise ValueError(f'Error in parsing periods and freq! Received periods = {period}, freq = {freq}. The string should be in the format of [a number][an English word representing a interval]. For more details, please visit https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases.')
    return period, freq


def retrieve_data(target_filename=None, root='price_data/archive/'):
    '''
    Retrieve data from the root directory as specified. This function is intended for the minute resolution dataset downloaded from Kaggle only (https://www.kaggle.com/tencars/392-crypto-currency-pairs-at-minute-resolution).
    Input:
        target_filename <str>: Defaults to None, meaning that it will extract all csv data in the directory. If specified, it will only extract that one specific file only. The target filename should include '.csv' too in the input.
        root <str>: Represents the directory where the price data is being stored.
    Return:
        df <pd.DataFrame>: A pd.DataFrame object where the index is [datetime], columns are [open, close, high, low, volume].
    '''
    if target_filename is None:
        price_data_dict = {}
        for f in os.listdir(root):
            if f.endswith('.csv'):
                df = pd.read_csv(root + f, usecols=['time', 'open', 'close', 'high', 'low', 'volume'])
                df['datetime'] = pd.to_datetime(df['time'], unit='ms')
                df.drop(columns=['time'], inplace=True)
                df = df.set_index('datetime')
                price_data_dict[f[:-4]] = df
        return price_data_dict
    else:
        df = pd.read_csv(root+target_filename, usecols=['time', 'open', 'close', 'high', 'low', 'volume'])
        df['datetime'] = pd.to_datetime(df['time'], unit='ms')
        df.drop(columns=['time'], inplace=True)
        df = df.set_index('datetime')
        return df


def build_ta_features(df, freq='1D', ta_list='all'):
    '''
    To build OHLCV (Open High Low Close Volume) features, and advanced features provided by TA-Lib.
    Input:
        df <pd.DataFrame>: A DataFrame object that contains columns ['timestamp', 'prices', 'market_caps', 'total_volumes']. It should be retreived from CoinGecko.
        freq <str>: A string that specifies the frequency of sampling. For different frequency notations, check https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases.
                    If set to None, it will not perform resampling.
        ta_list <list>: A list of techical analysis features to be built. For the whole list of feature names, check TA-Lib website: https://mrjbq7.github.io/ta-lib/funcs.html.
                        If ta_list is set to 'all', it will build all features available in TA-Lib. Otherwise, it will only build features as specified in the feature_list. If ta_list is set to None, it will not build any extra features in TA-Lib. It could be useful when you only want to resample it but not building any extra technical analysis features.
    Return:
        df <pd.DataFrame>: A DataFrame object where each column represents a unique feature (with name), and each row represents a sampled timestamp (with time).
    '''
    df = df.copy()
    if freq is not None:
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
    else:
        # First fill missing close price of the resampled df with previous close price
        df['close'] = df['close'].ffill()
        df['volume'] = df['volume'].fillna(0.0)

        # Then fill missing open high low price of the resampled df with the previous close price (copied to the same row)
        df = pd.concat([df['open'].fillna(df['close']),
                        df['high'].fillna(df['close']),
                        df['low'].fillna(df['close']),
                        df['close'],
                        df['volume']], axis=1)

    # Building advanced features using TA-Lib
    # For MAVP, it allows moving average with variable periods specified, we'll just skip this function.
    if ta_list is not None:
        if ta_list == 'all':
            ta_list = talib.get_functions()
        for i, x in enumerate(ta_list):
            try:
                output = eval('abstract.' + x + '(df)')
                output.name = x.lower() if type(output) == pd.core.series.Series else None
                df = pd.merge(df, pd.DataFrame(output), left_on = df.index, right_on = output.index)
                df = df.set_index('key_0')
            except:
                pass
        df.index.names = ['datetime']
    return df


def build_features(df, freq='1D', ta_list='all', ys=['1D-close'], roll=0):
    '''
    To build features for the inputted df by appending newly built features to the df. It calls build_ta_features to build techical analysis features and allows to build feature based on a rolling window. Also, it allows users to specify a list of intervals for binary up/down trend prediction via ys.
    Input:
        df <pd.DataFrame>: A pd.DataFrame object which inludes [datetime] as index, and [open, close, high, low, volume] in columns.
        ys <list>: A list of desired intervals for building binary up/down trend predictions. It should be in a format of '<interval>-<feature>' where the feature must be present in the df. Eg: ys=['1D-close', '3D-close']

    Return:
        x_df <pd.DataFrame>: A pd.DataFrame object that stores all the features.
        y_df <pd.DataFrame>: A pd.DataFrame object that stores all the predictions corresponding to ys.
    '''
    x_df = build_ta_features(df, freq=freq, ta_list=ta_list)
    # Adding rolling features
    columns = copy(df.columns)
    for i in range(roll):
        for c in columns:
            x_df[c + '-r' + str(i + 1)] = x_df[c].shift(i + 1)

    if ys is None:
        y_df = None
    else:
        # Adding labels
        y_df = x_df.copy() # Just to store x_df's index into y_df
        for target in ys:
            interval, feature = target.split('-')
            p, f = get_period_and_frequency(interval)
            y_df[target] = (x_df[feature].shift(periods=-p, freq=f) - x_df[feature]) > 0
        y_df = y_df.drop(columns=x_df.columns) # Features in x_df are dropped

        # Dropping all the np.inf and np.nan values in dataframes
        x_df = x_df.replace(np.inf, np.nan).dropna(how='all', axis=1).dropna(how='any', axis=0)
        y_df = y_df.replace(np.inf, np.nan).dropna(how='all', axis=1).dropna(how='any', axis=0)

        # Truncating series to make sure their indices are the same
        if len(x_df) > len(y_df):
            x_df = x_df.loc[y_df.index]
        else:
            y_df = y_df.loc[x_df.index]

        # Converting it to pd.Series if there is only one prediction target column
        if len(y_df.columns) == 1:
            y_df = y_df.iloc[:, 0]

    return x_df, y_df


if __name__ == '__main__':
    # First go to https://www.kaggle.com/tencars/392-crypto-currency-pairs-at-minute-resolution to download data zip file first
    # Unzip the file, put the folder called 'archive' under the 'price_data' directory
    root = 'price_data/archive/'
    price_data_dict = retrieve_data(root=root)

    for key in price_data_dict.keys():
        X, y = build_features(price_data_dict[key], freq='12H', ta_list=['ROC', 'MOM', 'EMA'], ys=['1D-close', '3D-close'], roll=2)
        print(X)
        print(X.shape)
        print(y)
        print(y.shape)
        break
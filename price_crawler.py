from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta
from time import sleep
import pickle as pkl
from os import path
import talib
from talib import abstract

cg = CoinGeckoAPI()

def get_data(address, start, end):

    '''
    Input (address <str> , start <timestamp>, end <timestamp>) -> DataFrame of price data
    This API wrapper wrap the CoinGecko API
    To get hourly data start and end must be within 90 days
    '''

    raw = cg.get_coin_market_chart_range_from_contract_address_by_id(id='ethereum', contract_address=address, vs_currency='usd', from_timestamp=start, to_timestamp=end)
    cleaned = {}
    cleaned['timestamp'] = [i[0] for i in raw['prices']]
    cleaned['prices'] = [i[1] for i in raw['prices']]
    cleaned['market_caps'] = [i[1] for i in raw['market_caps']]
    cleaned['total_volumes'] = [i[1] for i in raw['total_volumes']]
    return pd.DataFrame.from_dict(cleaned)


def update_token(address, start_date=datetime(2019, 1, 1)):

    '''
    Input(address <str>, start_date <datetime>) -> None
    Update the dataframe of the specified address within price_data directory
    If dataframe not exist crawl from start date and create a new one
    '''

    file_dir = 'price_data/' + address + '.pkl'
    now = datetime.now()

    if path.exists(file_dir):
        with open(file_dir, 'rb') as f:
            data, update_time = pkl.load(f)
            data = [data]
        start = update_time
        end = update_time + timedelta(days=80)
    else:
        start = start_date
        end = start_date + timedelta(days=80)
        data = []

    while now > end:
        st = datetime.timestamp(start)
        et = datetime.timestamp(end)
        data.append(get_data(address, st, et)) # Require time to be in timestamp format
        start = start + timedelta(days=80)
        end = end + timedelta(days=80)
        sleep(0.5)                             # To avoid getting blocked
    st = datetime.timestamp(start)
    et = datetime.timestamp(now)
    data.append(get_data(address, st, et))
    df = pd.concat(data, ignore_index=True)
    with open(file_dir, 'wb') as f:
        pkl.dump((df, now), f)                 # Save tuple (DataFrame, Update_Time) to pkl


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
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('date')

    # Building Open High Low Close Volume features for different frequencies
    ohlc_df = df.resample(freq)['prices'].agg(['first', 'max', 'min', 'last'])
    v_df = df.resample(freq)['total_volumes'].sum()
    df = pd.merge(ohlc_df, v_df, on='date')
    df.columns = ['open', 'high', 'low', 'close', 'volume']

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


def build_features(address, freq='12H', ta_list=None, ys={'1D-price': 2, '3D-price': 6}, rolling=3):

    '''
    To build features for the target address.
    Input(address <str>) -> DataFrame
    Read the craweled Dataframe of the specified address and add feature columns to it
    '''

    file_dir = 'price_data/' + address + '.pkl'
    with open(file_dir, 'rb') as f:
        df, update_time = pkl.load(f)

    df = build_ta_features(df, freq=freq, ta_list=ta_list)

    # Add rolling features
    for i in range(rolling):
        for c in df.columns:
            df[c + '-r' + str(i + 1)] = df[c].shift(i + 1)

    # Add labels
    for target_name, period in ys.items():
        df[target_name] = (df['close'].shift(-period) - df['close']) > 0

    df = df.dropna()
    return df


if __name__ == '__main__':
    address = '0x514910771af9ca656af840dff83e8264ecf986ca'
    update_token(address)
    df = build_features(address, freq='12H')
    print(df.tail())

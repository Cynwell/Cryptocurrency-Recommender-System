from pycoingecko import CoinGeckoAPI
import pandas as pd
from datetime import datetime, timedelta
from time import sleep
import pickle as pkl
from os import path

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


def create_features(address):

    '''
    Input(address <str>) -> DataFrame
    Read the craweled Dataframe of the specified address and add feature columns to it
    '''

    file_dir = 'price_data/' + address + '.pkl'
    with open(file_dir, 'rb') as f:
        df, update_time = pkl.load(f)

    # Features
    



create_features(address='0x514910771af9ca656af840dff83e8264ecf986ca')

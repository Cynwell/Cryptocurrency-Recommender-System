import pandas as pd
import requests

from price_crawler import update_token
import trend as skl
import rnn_trend as rnn

def update_all(tokens_file='tokens.csv'):

    tokens = pd.read_csv(tokens_file)
    for address, name in zip(tokens['Address'], tokens['Name']):
        try:
            update_token(address)
        except:
            print(f'Cannot get price of {name}')



if __name__ == '__main__':
    # update_all()
    update_token('0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e'.lower())
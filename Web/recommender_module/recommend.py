import numpy as np
import pickle as pk
import os

from .crawler import get_address_transactions
from .algorithm import UserKNN
from .price_crawler import build_features, update_token

API_KEY = 'UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6'
TA_FEATURES = ['ROC', 'MOM', 'EMA', 'SMA', 'VAR', 'MACD', 'ADX', 'RSI']

class Profile:

    def __init__(self, address):
        self.address = address
        self.status = 'Ok'
        self.user_knn_results = None
        self.user_knn_scores = None
        self.predict_results = None


def recommend(uid, address, profiles, data, tokens):

    # Get transactions record of given address
    address = address.lower()
    transactions = get_address_transactions(address, API_KEY)

    # Create the server side profile for the user
    p = Profile(address)
    profiles[uid] = p

    # Error occur while getting transaction records
    if isinstance(transactions, str):
        p.status = transactions
        return

    # Create the vector representation of transaction records
    transactions = transactions[transactions['to'] == address]
    transactions['contractAddress'] = transactions['contractAddress'].str.lower()
    bought = transactions['contractAddress'].value_counts()
    vec = np.array([bought.loc[t] if t in bought.index else 0 for t in tokens.index])

    # Evaluate and store results from UserKNN
    results, scores = UserKNN(data, vec, tokens.index)

    # Handle the case where there is an error in the data
    if isinstance(results, str):
        p.status = results
        return

    # Get price prediction for the results
    predictions = []
    for r in results:
        token_predict = []
        symbol = tokens.loc[r, 'CoinGeckoID']
        if os.path.exists('models/' + symbol + '-1D-close.pkl'):
            for target in ['-1D-close.pkl', '-3D-close.pkl', '-7D-close.pkl']:
                f = open('models/' + symbol + target, 'rb')
                model, cfg = pk.load(f)
                X, y = build_features(symbol, freq=cfg['delta'], ta_list=TA_FEATURES, roll=cfg['roll'], ys=['3D-close'])
                y = model.predict(X[-2:-1])[0]
                token_predict.append(int(y))
            predictions.append(token_predict)
        else:
            predictions.append(['NA', 'NA', 'NA'])

    p.user_knn_results = results
    p.user_knn_scores = scores
    p.predict_results = predictions



# For testing purpose
if __name__ == '__main__':
    print(os.getcwd())
    import pandas as pd
    import pickle as pk
    TOKENS = pd.read_csv('data/tokens.csv')
    TOKENS['Address'] = TOKENS['Address'].str.lower()
    TOKENS.set_index('Address', inplace=True)
    with open('data/user_array.pkl', 'rb') as usr:
        USER_ARRAY = pk.load(usr)
    uid = '1234578'
    address = '0x3cD74f51142F6a740ae9211149Fb338463882Bae'
    profiles = {}
    
    recommend(uid, address, profiles, USER_ARRAY, TOKENS)
    print(profiles[uid].user_knn_results)
    print(profiles[uid].predict_results)
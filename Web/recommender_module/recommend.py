import numpy as np
from .crawler import get_address_transactions
from .algorithm import UserKNN

API_KEY = 'UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6'

class Profile:

    def __init__(self, address):
        self.address = address
        self.status = 'Ok'
        self.user_knn_results = None

def recommend(uid, address, profiles, data, tokens):

    # Get transactions record of given address
    address = address.lower()
    tx = get_address_transactions(address, API_KEY)

    # Create the server side profile for the user
    p = Profile(address)
    profiles[uid] = p

    # Error occur while getting transaction records
    if isinstance(tx, str):
        p.status = tx
        return

    # Create the vector representation of transaction records
    tx = tx[tx['to'] == address]
    tx['contractAddress'] = tx['contractAddress'].str.lower()
    bought = tx['contractAddress'].value_counts()
    vec = np.array([bought.loc[t] if t in bought.index else 0 for t in tokens])

    # Evaluate and store results from UserKNN
    results = UserKNN(data, vec, tokens)
    if isinstance(results, str):
        p.status = results
    else:
        p.user_knn_results = results


# For testing purpose
if __name__ == '__main__':
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
    
    recommend(uid, address, profiles, USER_ARRAY, TOKENS.index)
    t, s = profiles[uid].user_knn_results
    print(t)
    print(s)
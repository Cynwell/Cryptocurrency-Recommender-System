import pickle as pk
import os

from crawler import Client_v1

class Scorer:

    '''
    Class for calculating similarity between user and another address
    '''
    
    def __init__(self, user):
        self.user = user

    def __call__(self, other):

        '''
        Input(other <Pandas.Series>) -> float [0..1]
        Overloaded the () operator
        '''

        s = 0
        for i in self.user.index:
            if i in other.index:
                s += self.user.loc[i] * other.loc[i]
        return s

WALLET_NO = 10   # No of similar wallet address to be considered
MIN_SCORE = 0.01 # Minimum score for valid recommendation
REF_NO = 3       # No of token to recommend

def recommend(user_address):

    '''
    Input(user_address <str>) -> list
    Function for making recommendations
    Addresses of top N recommended tokens return as a list of string
    '''

    # Obtain user data
    f = open('CF_data', 'rb')
    cf_data = pk.load(f)
    client = Client_v1(api_key='UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6', verbose=0)

    # Process to correct format
    user_address = user_address.lower()
    trasactions = client.get_token_transactions_by_address(user_address)
    bought = trasactions[trasactions['to'] == user_address]
    if len(bought) == 0:
        print('Error')
        return
    profile = bought['contractAddress']
    profile = profile.value_counts(normalize=True)
    score = Scorer(profile)
    cf_data = sorted(cf_data, key=score, reverse=True) # Find the most similar address to user
    while True:
        if score(cf_data[0]) == 1.0:
            cf_data.pop(0)
        elif score(cf_data[0]) < MIN_SCORE:
            print('Insufficient data')
            return
        else:
            break
    occurence = {}   # For counting token appearing in similar address but not user address
    for wallet in cf_data[:WALLET_NO]:
        for token, count in wallet.iteritems():
            if token in profile.index:
                pass
            elif token in occurence:
                occurence[token] += count
            else:
                occurence[token] = count
    tokens = list(occurence.keys())
    tokens = sorted(tokens, key=occurence.get, reverse=True)
    return tokens[:REF_NO]


r = recommend('0xfef30F53FB6C34B9034e0A898921806C84B4Ae1f')
print(r)






    



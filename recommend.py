import pickle as pk
import os

from crawler import Client_v1

class Scorer:
    
    def __init__(self, user):
        self.user = user

    def __call__(self, other):
        s = 0
        for i in self.user.index:
            if i in other.index:
                s += self.user.loc[i] * other.loc[i]
        return s

WALLET_NO = 10
MIN_SCORE = 0.01
REF_NO = 3

def recommend(user_address):
    f = open('CF_data', 'rb')
    cf_data = pk.load(f)
    client = Client_v1(api_key='UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6', verbose=0)

    user_address = user_address.lower()
    trasactions = client.get_token_transactions_by_address(user_address)
    bought = trasactions[trasactions['to'] == user_address]
    if len(bought) == 0:
        print('Error')
        return
    profile = bought['contractAddress']
    profile = profile.value_counts(normalize=True)
    score = Scorer(profile)
    cf_data = sorted(cf_data, key=score, reverse=True)
    while True:
        if score(cf_data[0]) == 1.0:
            cf_data.pop(0)
        elif score(cf_data[0]) < MIN_SCORE:
            print('Insufficient data')
            return
        else:
            break
    occurence = {}
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






    



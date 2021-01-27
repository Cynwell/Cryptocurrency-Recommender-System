import pickle as pk
import os
from time import time

import numpy as np


WALLET_NO = 1000    # No of similar wallet address to be considered
MIN_SCORE = 0.5     # Minimum score for valid recommendation
NO_RECOMMEND = 5    # No of token to recommend


def UserKNN(user_array, vec, all_tokens):

    # Compute similarity score
    scores = user_array.dot(vec)

    # Filter out entries that do not reach minimum score
    arr = user_array[scores > MIN_SCORE]
    scores = scores[scores > MIN_SCORE]

    # Filter away entries buying exacly the same tokens 
    binary_arr = arr > 0
    binary_vec = vec > 0
    different = np.abs(binary_arr != binary_vec).sum(axis=1) > 0
    arr = arr[different]
    scores = scores[different]

    if len(arr) < WALLET_NO:
        return 'Insufficient Address Data.'

    # Sum the token scores from the top WALLET_NO wallets
    token_scores = np.zeros(100)
    for i in range(WALLET_NO):
        j = np.argmax(scores)
        token_scores += arr[j]
        scores[j] = 0

    # Find the top 5 tokens
    tokens = []
    recommend_scores = []
    for i in range(NO_RECOMMEND):
        j = np.argmax(token_scores)
        tokens.append(all_tokens[j])
        recommend_scores.append(token_scores[j])
        token_scores[j] = 0
    
    return tokens, recommend_scores


def TokenKNN(user_address):

    '''
    Input(user_address <str>) -> list
    Function for making recommendations
    Addresses of top N recommended tokens return as a list of string
    '''

    f = open('tcf_data.pkl', 'rb')
    token_address, token_sim = pk.load(f)
    # client = Client_v3(api_key='UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6', verbose=0)

    # Process to correct format
    user_address = user_address.lower()
    # trasactions = client.get_transaction_by_address(user_address)
    trasactions = trasactions[['tokenName', 'contractAddress', 'from', 'to', 'value']]
    bought = trasactions[trasactions['to'] == user_address]
    profile = bought['contractAddress'].value_counts(normalize=True)

    recommendation = {}
    for a1 in token_address:
        if a1 in profile.index:
            continue
        for a2 in profile.index:
            if a1 + a2 in token_sim:
                recommendation[a1] = profile.loc[a2] * token_sim[a1 + a2]
    
    return sorted(list(recommendation.keys()), key=recommendation.get)


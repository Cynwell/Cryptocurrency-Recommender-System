import logging
import pickle as pkl
import os
from crawler import Client_v3

root = 'transaction_data/token2/'
if not os.path.exists(root):
    print(f'Created {root}.')
    os.makedirs(os.path.abspath(root))
logging.basicConfig(filename=root+'20200916_new.log',
                             level=logging.INFO,
                             format='%(asctime)-15s %(levelname)-8s %(message)s')

if os.path.exists(root+'node_list.txt'):
    answer = input(f'{root}node_list.txt exists in the directory! Are you sure to overwrite node_list.txt (Y/N)? ')
    if answer not in ['Y', 'y']:
        raise NameError('Please backup node_list.txt and other files first before running the crawler!')

# Put top 20 token addresses here
token_address_list = ['0xdd974d5c2e2928dea5f71b9825b8b646686bd200', # Kyber Network (KNC)
                      '0x514910771af9ca656af840dff83e8264ecf986ca', # ChainLink (LINK)
                      '0xe41d2489571d322189246dafa5ebde1f4699f498', # 0x (ZRX)
                      '0xd46ba6d942050d489dbd938a2c909a5d5039a161', # Ampleforth (AMPL)
                      '0x221657776846890989a759ba2973e427dff5c9bb'] # Augur v2 (REP)

transaction_data_dict = dict()
client = Client_v3(verbose=1)
node_list = []
try:
    for token_address in token_address_list:
        transaction_data = client.get_transaction_by_token(token_address)
        transaction_data_dict[token_address] = transaction_data
        node_list.extend(transaction_data['from_address'].tolist())
        node_list.extend(transaction_data['to_address'].tolist())
    node_list = list(set(node_list))
except Exception as e:
    print(e)
finally:
    with open(root+'transaction_data_by_token_address_dict.pkl', 'wb') as f:
        pkl.dump(transaction_data_dict, f)
        print(f'Saved transaction data related to token addresses to "{root}transaction_data_by_token_address_dict.pkl".')
    with open(root+'node_list.txt', 'w') as f:
        for node in node_list:
            f.writelines(node + '\n')
        print(f'Saved nodes to "{root}node_list.txt".')
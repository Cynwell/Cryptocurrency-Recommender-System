import logging
import pickle as pkl
import os
from crawler import Client_v3

root = 'transaction_data/token4/'
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
token_address_list = [
    '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e', # YFI
    '0xba100000625a3754423978a60c9317c58a424e3d'  # BAL
] 

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
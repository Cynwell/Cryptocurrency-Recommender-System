import pandas as pd
import etherscan as es
import logging
import pickle as pkl
import time
import requests
import random
import os
import argparse


class Client_v1(es.Client):
    '''
    Extra functions based on etherscan.Client module.
    '''
    def __init__(self, api_key='', verbose=1):
        super(Client_v1, self).__init__(api_key)
        self.api_key = api_key
        self.last_execution = 0
        self.verbose = verbose
        self.MAX_TRIAL_COUNT = 10
        self.interval = 0.5 if self.api_key == '' else 0
        pass

    def get_token_transactions_by_address(self, address):
        '''
        Get token transaction by the wallet address.
        Input:
            address <str>: the wallet address
        Return:
            record <pd.DataFrame>: a dict that contains all the related data with the address.
        '''
        exceed_limit_error = False
        trial_count = 0
        url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=999999999&sort=asc&apikey={self.api_key}'
        if self.verbose >= 1:
            logging.info(f'Retrieving node with address {node_list[i]} from URL: {url}')
            print(f'Retrieving node with address {node_list[i]} from URL: {url}')
        while True:
            if time.time() - self.last_execution < self.interval:
                time.sleep(self.interval)
            try:
                data = pd.read_json(url)
                self.last_execution = time.time()
                exceed_limit_error = False
            except:
                exceed_limit_error = True
                trial_count += 1
                logging.info(f'Max rate limit reached because sending requests within {time.time() - self.last_execution:.2f}s. trial_count = {trial_count}')
                if self.verbose == 2:
                    print(f'Max rate limit reached because sending requests within {time.time() - self.last_execution:.2f}s. trial_count = {trial_count}')
            if not exceed_limit_error or trial_count >= self.MAX_TRIAL_COUNT:
                break


        record = pd.DataFrame(columns=['blockNumber', 'timeStamp', 'hash', 'nonce', 'blockHash', 'from', 'contractAddress', 'to', 'value', 'tokenName', 'tokenSymbol', 'tokenDecimal', 'transactionIndex', 'gas', 'gasPrice', 'gasUsed', 'cumulativeGasUsed', 'input', 'confirmations'])
        if 0 in data['status'].unique():
            logging.warning(f'ADDRESS: {address}')
            logging.warning(f'RECORD: {record}')
        record = pd.json_normalize(data['result'])
        return record


def get_neighbor_nodes(record):
    '''
    Get a list of nodes that are related to the account in the record.
    Input:
        record <pd.DataFrame>: a dict that contains all the related data with the address.
    Return:
        unique_node_list <list>: a list that contains unique nodes encountered during the scanning process.
    '''
    node_list = [*record['from'].tolist(), *record['to'].tolist()]
    unique_node_list = list(set(node_list))
    return unique_node_list


# Python script
parser = argparse.ArgumentParser()

# Required parameters
parser.add_argument('--node_count', default=5, type=int, required=False,
                    help='Number of nodes to be retrieved in a single time run.')
parser.add_argument('--initial_node', default='0x0000000000000000000000000000000000000000', type=str, required=False,
                   help='The initial node to start crawling.')
parser.add_argument('--verbose', default=1, type=int, required=False,
                   help='0: No debug information will be displayed on the console; 1: Some information; 2: All information.')
parser.add_argument('--api_key', default='', type=str, required=False,
                   help='The key for retrieving data via the API.')
args = parser.parse_args()

# # Jupyter Notebook
# class parser:
#     def __init__(self):
#         self.node_count = 500
#         self.initial_node = '0x0000000000000000000000000000000000000000'
#         self.verbose = 1
#         self.api_key = 'UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6'
# args = parser()


root = 'transaction_data/'
if not os.path.exists(root):
    os.makedirs(os.path.abspath(root))
logging.basicConfig(filename=root+'20200830.log',
                             level=logging.INFO,
                             format='%(asctime)-15s %(levelname)-8s %(message)s')
try:
    node_list = []
    with open(root+'node_list.txt', 'r') as f:
        for line in f:
            node_list.append(line.splitlines()[0])
    print('Retrieved node file from disk.')
except FileNotFoundError:
    print('Node file not found.')
finally:
    if len(node_list) == 0:
        print('Initialized the node list with the default node address:', args.initial_node)
        node_list.append(args.initial_node)

try:
    explored_nodes = dict()
    with open(root+'explored_nodes_keys.txt', 'r') as f:
        for line in f:
            explored_nodes[line.splitlines()[0]] = 'Explored' # Just fill the corresponding value with some random contents, such that it exists in the dictionary.
    print('Retrieved explored nodes dictionary keys from disk.')
except:
    print('Explored nodes dictionary keys file not found.')

client = Client_v1(api_key=args.api_key, verbose=args.verbose)

try:
    for count in range(args.node_count):
        try:
            i = random.randint(0, len(node_list)-1)                         # Get a node from node_list using index i
            print(f'Progress: {count+1}/{args.node_count} ', end='')
            record = client.get_token_transactions_by_address(node_list[i]) # Process the node
            neighbor_nodes = get_neighbor_nodes(record)                     # Retrieve its neighbor nodes
            explored_nodes[node_list[i]] = record                           # Add node i to explored_nodes
            node_list.remove(node_list[i])                                  # Remove node i from the node_list (because it has been explored)
            for node in neighbor_nodes:
                if node not in explored_nodes.keys():
                    node_list.append(node)                                  # Append neighbor nodes to node_list, given that they are not in explored_dict
            node_list = list(set(node_list))                                # Select unique neighbor nodes
        except Exception as e:
            logging.error(e)
except:
    pass
finally:
    # Writing upated node list to file
    with open(root+'node_list.txt', 'w') as f:
        for node in node_list:
            f.writelines(node + '\n')
        print('Saved nodes to "node_list.txt".')

    with open(root+'explored_nodes_keys.txt', 'w') as f:
        for node in explored_nodes.keys():
            f.writelines(node + '\n')
        print('Saved exlpored node addresses to "explored_nodes_keys.txt".')
    with open(root+f'explored_nodes_dict_{time.strftime("%Y%m%d%H%M")}.pkl', 'wb') as f:
        pkl.dump(explored_nodes, f)
    print(f'Saved explored node dictionary to "{root}explored_nodes_dict_{time.strftime("%Y%m%d%H%M")}.pkl".')
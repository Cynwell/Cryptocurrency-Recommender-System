import logging
import pickle as pkl
import time
import random
import os
import argparse
from crawler import Client_v3

# Python script
parser = argparse.ArgumentParser()

# Required parameters
parser.add_argument('--root', default='transaction_data/token1/', type=str, required=True,
                    help='The path to the destination folder.')
parser.add_argument('--node_count', default=5, type=int, required=False,
                    help='Number of nodes to be retrieved in a single time run.')
parser.add_argument('--verbose', default=1, type=int, required=False,
                   help='0: No debug information will be displayed on the console; 1: Some information; 2: All information.')
parser.add_argument('--api_key', default='', type=str, required=False,
                   help='The key for retrieving data via the API.')
args = parser.parse_args()


root = args.root
if not os.path.exists(root):
    os.makedirs(os.path.abspath(root))
logging.basicConfig(filename=root+'20200919_new.log',
                             level=logging.INFO,
                             format='%(asctime)-15s %(levelname)-8s %(message)s')
try:
    node_list = []
    with open(root+'node_list.txt', 'r') as f:
        for line in f:
            node_list.append(line.splitlines()[0])
    print('Retrieved node file from disk.')
    node_count = min(args.node_count, len(node_list))
except FileNotFoundError:
    raise FileNotFoundError('node_list.txt was not found! Please regenerate the file by using token_crawler.py!')

try:
    explored_nodes_list = []
    with open(root+'explored_nodes_keys.txt', 'r') as f:
        for line in f:
            explored_nodes_list.append(line.splitlines()[0]) # Just fill the corresponding value with some random contents, such that it exists in the dictionary.
    print('Retrieved explored nodes dictionary keys from disk.')
except:
    print('Explored nodes dictionary keys file not found.')

client = Client_v3(api_key=args.api_key, verbose=args.verbose)
explored_nodes_dict = dict()
try:
    count = 0
    while count < node_count:
        try:
            i = random.randint(0, len(node_list)-1)                         # Get a node from unexplored node_list using index i
            print(f'Progress: {count+1}/{node_count} ', end='')
            record = client.get_transaction_by_address(node_list[i])        # Process the node
            explored_nodes_dict[node_list[i]] = record                      # Add node i to explored_nodes_dict
            explored_nodes_list.append(node_list[i])                        # Add node i to explored_nodes_list
            node_list.remove(node_list[i])                                  # Remove node i from the unexplored node_list (because it has just been explored)
            count += 1                                                      # Increment to count only when it is a success retrieval of node information
        except Exception as e:
            logging.error(e)
except:
    pass
finally:
    pass
    # Writing upated node list to file
    with open(root+'node_list.txt', 'w') as f:
        for node in node_list:
            f.writelines(node + '\n')
        print('Saved nodes to "node_list.txt".')
    with open(root+'explored_nodes_keys.txt', 'w') as f:
        for node in explored_nodes_list:
            f.writelines(node + '\n')
        print('Saved exlpored node addresses to "explored_nodes_keys.txt".')
    with open(root+f'explored_nodes_dict_{time.strftime("%Y%m%d%H%M")}.pkl', 'wb') as f:
        pkl.dump(explored_nodes_dict, f)
    print(f'Saved explored node dictionary to "{root}explored_nodes_dict_{time.strftime("%Y%m%d%H%M")}.pkl".')
import pickle as pkl
import os
import pandas as pd


root = 'transaction_data/'

# Read all .pkl dictionary files under the defined root directory
dictionary_files = []
for _, _, filenames in os.walk(os.path.join(os.getcwd(), root)):
    for filename in filenames:
        if filename.endswith('.pkl'):
            dictionary_files.append(filename)

# Merge all dictionary files into one dictionary
explored_nodes = {}
for filename in dictionary_files[:1]:
    with open(root+filename, 'rb') as f:
        tmp_dict = pkl.load(f)
        pop_list = [k for k, v in tmp_dict.items() if type(v) == str and v == 'Explored']
        for node in pop_list:
            tmp_dict.pop(node) # delete nodes that have been marked as "Explored"
        explored_nodes = {**explored_nodes, **tmp_dict} # merge dict

# Create a table containing all transansaction data and do basic statistics
transaction_data = pd.concat([v for v in explored_nodes.values()], ignore_index=True)
unique_nodes = [*transaction_data['from'].tolist(), *transaction_data['to'].tolist()]
unique_nodes = set(unique_nodes)

print('Number of explored nodes:', len(explored_nodes))
print('Number of total nodes:', len(unique_nodes))
print('Number of edges:', transaction_data.shape[0])

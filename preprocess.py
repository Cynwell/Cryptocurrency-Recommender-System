import pickle as pkl
import os

def getAddressType(x):
    pass


def aggregate():

    '''
    Process raw transaction data into the format useful for collasborative filtering
    Stored to cf_data.pkl
    '''

    root = 'transaction_data/'

    # Read all .pkl dictionary files under the defined root directory
    dictionary_files = []
    for _, _, filenames in os.walk(os.path.join(os.getcwd(), root)):
        for filename in filenames:
            if filename.endswith('.pkl'):
                dictionary_files.append(filename)

    # Merge all dictionary files into one dictionary
    explored_nodes = {}
    for filename in dictionary_files:
        with open(root+filename, 'rb') as f:
            tmp_dict = pkl.load(f)
            pop_list = [k for k, v in tmp_dict.items() if type(v) == str and v == 'Explored']
            for node in pop_list:
                tmp_dict.pop(node) # delete nodes that have been marked as "Explored"
            explored_nodes = {**explored_nodes, **tmp_dict} # merge dict

    output = []
    for k, df in explored_nodes.items():
        df = df[df['to'] == k]
        token_bought = df['contractAddress']
        output.append(token_bought.value_counts(normalize=True))

    print(len(output))

    f = open('cf_data', 'wb')
    pkl.dump(output, f)

aggregate()

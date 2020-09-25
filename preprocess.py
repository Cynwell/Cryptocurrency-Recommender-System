import pickle as pkl
import os

def getAddressType(x):
    pass


def aggregate():

    '''
    Process raw transaction data into the format useful for collasborative filtering
    Stored to cf_data.pkl
    '''

    data_folder = 'transaction_data/'

    # Read all .pkl dictionary file names under the defined root directory
    dictionary_files = []
    for filename in os.listdir(data_folder):
        if filename.endswith('.pkl'):
            dictionary_files.append(filename)

    # Read token frequency statistics of each address from pkl
    output = []
    for filename in dictionary_files:
        with open(data_folder + filename, 'rb') as f:
            tmp_dict = pkl.load(f)
            for k, df in tmp_dict.items():
                df = df[df['to'] == k]
                token_bought = df['contractAddress']
                output.append(token_bought.value_counts(normalize=True))

    print('There are in total', len(output), 'lines')

    # Save result to a pkl
    f = open('cf_data.pkl', 'wb')
    pkl.dump(output, f)


if __name__ == '__main__':
    aggregate()
    
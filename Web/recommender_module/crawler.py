import pandas as pd
import time

def get_address_transactions(address, api_key, interval=0.5, max_trial=10):
    '''
    Get ERC-20 token transactions by the wallet/smart contract address. Corresponds to https://etherscan.io/address/.
    Input:
        address <str>: the wallet address
        api_key <str>: API key for etherscan 
    Return:
        record <pd.DataFrame>: a dict that contains all the related data with the address.
    '''

    trial_count = 0
    last_execution = time.time()
    url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=999999999&sort=desc&apikey={api_key}'
    while True:
        if time.time() - last_execution < interval:
            time.sleep(interval)
        try:
            last_execution = time.time()
            data = pd.read_json(url)
            break
        except ValueError:
            return 'Address Invalid.'
        if trial_count >= max_trial:
            return 'Cannot Get Adress Data.'

    record = pd.DataFrame(columns=['blockNumber', 'timeStamp', 'hash', 'nonce', 'blockHash', 'from', 'contractAddress', 'to', 'value', 'tokenName', 'tokenSymbol', 'tokenDecimal', 'transactionIndex', 'gas', 'gasPrice', 'gasUsed', 'cumulativeGasUsed', 'input', 'confirmations'])
    record = pd.json_normalize(data['result'])
    
    record['value'] = record.apply(lambda x: int(x['value']) / 10 ** int(x['tokenDecimal']), axis=1)
    record.drop('tokenDecimal', axis=1, inplace=True)
    return record


# For testing purpose
if __name__ == '__main__':
    data = get_address_transactions('0x3cD74f51142F6a740ae9211149Fb338463882Bae', 'UCJ24GP9ICCR28QNPDNCXZ27VHWIG442F6')
    print(data)


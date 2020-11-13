import pandas as pd
import logging
import time
import cloudscraper
from bs4 import BeautifulSoup
import argparse


class Client_v3:
    '''
    An updated crawler which merged v1 and v2.
    An updated crawler that could bypass CloudFlare and scrape Etherscan.io websites.
    This crawler is designed to retrieve transaction records of tokens.
    '''
    def __init__(self, api_key='', verbose=1):
        self.api_key = api_key
        self.last_execution = 0
        self.verbose = verbose
        self.MAX_TRIAL_COUNT = 10
        self.interval = 0.5 if self.api_key == '' else 0

    def get_transaction_by_address(self, address):
        '''
        Get ERC-20 token transactions by the wallet/smart contract address. Corresponds to https://etherscan.io/address/.
        Input:
            address <str>: the wallet address
        Return:
            record <pd.DataFrame>: a dict that contains all the related data with the address.
        '''
        exceed_limit_error = False
        trial_count = 0
        url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=999999999&sort=desc&apikey={self.api_key}'
        if self.verbose >= 1:
            logging.info(f'Retrieving node with address {address} from URL: {url}')
            print(f'Retrieving node with address {address} from URL: {url}')
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
        record['value'] = record.apply(lambda x: int(x['value']) / 10 ** int(x['tokenDecimal']), axis=1)
        record.drop('tokenDecimal', axis=1, inplace=True)

        # Append a new column called isUser
        url = f'https://api.etherscan.io/api?module=proxy&action=eth_getCode&address={address}&tag=latest&apikey={self.api_key}'
        user = pd.read_json(url, orient='index').transpose()
        user_type = True if user['result'][0] == '0x' else False
        logging.info(f'Node address {address} is a user: {user_type}, retrieved from {url}')
        if self.verbose == 2:
            print(f'Node address {address} is a user: {user_type}, retrieved from {url}')
        record['isUser'] = user_type
        return record

    def get_transaction_by_token(self, address):
        '''
        Get transactions of a ERC20 token by the token/smart contract address. Corresponds to https://etherscan.io/token/.
        Input:
            address <str>: the token/smart contract address
        Return:
            record <pd.DataFrame>: a DataFrame object that contains all the related transaction data with the address, including  columns ['txn_hash' <str>, 'transaction_date' <str>, 'from_address' <str>, 'to_address' <str>, 'quantity' <float>].
        '''
        # Scraping the initial page for retrieving the sid (which is a JavaScript variable)
        trial_count = 0
        while True:
            error = False
            try:
                url = f'https://etherscan.io/token/{address}'
                scraper = cloudscraper.create_scraper()
                logging.info(f'Scraping the initial page of token with address {address} from URL: {url}')
                if self.verbose >= 1:
                    print(f'Scraping the initial page of token with address {address} from URL: {url}')
                response = scraper.get(url.format(address))
                page = response.text
                sid = page[page.find('sid')+7:page.find('sid')+39]
                if response.status_code == 200:
                    self.last_execution = time.time()
            except Exception as e:
                logging.info(f'An error encountered while scraping initial page of token address {address} with URL: {url}. Last request was sent in {time.time() - self.last_execution:.2f}s. trial_count = {trial_count}')
                logging.info(e)
                logging.info(response, page)
                if self.verbose == 2:
                    print(f'An error encountered while scraping initial page of token address {address} with URL: {url}. Last request was sent in {time.time() - self.last_execution:.2f}s. trial_count = {trial_count}')
                    print(e)
                    print(response, page)
                error = True
                trial_count += 1
            finally:
                if error:
                    if time.time() - self.last_execution < self.interval:
                        time.sleep(self.interval)
                        logging.info(f'Sleeping for {self.interval}s before making another request')
                    if trial_count > self.MAX_TRIAL_COUNT:
                        scraper = cloudscraper.create_scraper()
                        logging.info('Replacing with a new scraper')
                else:
                    break

        # Scraping transaction records, given address of the token
        p = 1
        page_count = 'Unknown' # unknown at the moment, until the first retrieval of transaction records. It'll become int.
        txn_hash = []
        transaction_date = []
        from_address = []
        to_address = []
        quantity = []
        trial_count = 0
        while True:
            error = False
            try:
                url = f'https://etherscan.io/token/generic-tokentxns2?contractAddress={address}&mode=&sid={sid}&m=normal&p={p}'
                logging.info(f'Scraping transaction records of token with address {address} from URL: {url}')
                if self.verbose >= 1:
                    print(f'Progress: {p}/{page_count} ', end='')
                    print(f'Scraping transaction records of token with address {address} from URL: {url}')
                response = scraper.get(url.format(address, sid, p))
                page = response.text
                soup = BeautifulSoup(page, 'lxml')
                self.last_execution = time.time()
                if response.status_code == 200:
                    self.last_execution = time.time()

                # Retrieve page count
                if page_count == 'Unknown':
                    page_count = int(soup.findAll('strong')[1].text)

                # Retrieve data in the table
                table = soup.findAll('tr')[1:]
                for tr in table: # scan every row in the table
                    txn_hash.append(tr.find('a').text)
                    transaction_date.append(tr.find('span', attrs={'data-placement': 'bottom'}).text)
                    from_address.append(tr.findAll('a', attrs={'class': 'hash-tag text-truncate'})[0]['href'][-42:])
                    to_address.append(tr.findAll('a', attrs={'class': 'hash-tag text-truncate'})[1]['href'][-42:])
                    quantity.append(float(tr.findAll('td')[-2].text.replace(',', '')))
                trial_count = 0
            except Exception as e:
                logging.info(f'An error encountered while scraping transaction record of token address {address} from URL: {url}. Last request was sent in {time.time() - self.last_execution:.2f}s. trial_count = {trial_count}')
                print(e)
                print(response, page)
                error = True
                trial_count += 1
            finally:
                if error:
                    if time.time() - self.last_execution < self.interval:
                        time.sleep(self.interval)
                        logging.info(f'Sleeping for {self.interval}s before making another request')
                    if trial_count > self.MAX_TRIAL_COUNT:
                        scraper = cloudscraper.create_scraper()
                        logging.info('Replacing with a new scraper')
                else:
                    # Check whether it is the last page of available transaction records
                    if p >= page_count:
                        break
                    else:
                        p += 1

        # Combine into a pd.DataFrame
        transaction_record = pd.DataFrame.from_dict({'txn_hash': txn_hash, 'transaction_date': transaction_date, 'from_address': from_address, 'to_address': to_address, 'quantity': quantity})
        return transaction_record

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
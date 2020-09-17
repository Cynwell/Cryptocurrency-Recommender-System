import pandas as pd
import logging
import pickle as pkl
import time
import os
import cloudscraper
from bs4 import BeautifulSoup


class Client_v2:
    '''
    An updated crawler that could bypass CloudFlare and scrape Etherscan.io websites.
    This crawler is designed to retrieve transaction records of tokens.
    '''
    def __init__(self, verbose=1):
        self.last_execution = 0
        self.verbose = verbose
        self.MAX_TRIAL_COUNT = 10
        self.interval = 0.5

    def get_transactions_by_token(self, address):
        '''
        Get transactions of a specific token by the token/smart contract address. Corresponds to https://etherscan.io/token/.
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


root = 'transaction_data/token/'
if not os.path.exists(root):
    os.makedirs(os.path.abspath(root))
logging.basicConfig(filename=root+'20200916.log',
                             level=logging.INFO,
                             format='%(asctime)-15s %(levelname)-8s %(message)s')

if os.path.exists(root+'node_list.txt'):
    answer = input(f'{root}node_list.txt exists in the directory! Are you sure to overwrite node_list.txt (Y/N)?')
    if answer not in ['Y', 'y']:
        raise NameError('Please backup node_list.txt and other files first before running the crawler!')

# Put top 20 token addresses here
token_address_list = ['0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2', # Maker (MKD)
                      '0x80fB784B7eD66730e8b1DBd9820aFD29931aab03', # Aave (LEND)
                      '0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f', # Synthetix Network Token (SNX)
                      '0x6b175474e89094c44da98b954eedeac495271d0f', # Dai (DAI)
                      '0xc00e94cb662c3520282e6f5717214004a7f26888'] # Compound (COMP)

transaction_data_dict = dict()
client = Client_v2(verbose=1)
node_list = []
try:
    for token_address in token_address_list:
        transaction_data = client.get_transactions_by_token_address(token_address)
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
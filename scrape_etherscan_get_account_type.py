import cloudscraper
from bs4 import BeautifulSoup
import time


def getAddressType(address_list):
    '''
    Get types of a list of addresses. If it is a user node, return true, else false.
    Problem: Unverified contracts behaves same as user accounts, which returns exactly the same data.
    Input:
    address_list <list>: A list of string which are addresses.
    
    Return:
        type_list <list>: A list of boolean values indicating whether it is a user account address or not.
    
    '''
    MAX_FAIL_COUNT = 10
    # Type checking
    if type(address_list) == str:
        address_list = [address_list]
    elif type(address_list) != list:
        try:
            address_list = list(addrss)
        except TypeError:
            raise TypeError('Expected address_list to be a 1D list of string!')

    url = 'https://etherscan.io/address/{}'
    type_list = []
    # Start looping through the address_list
    for i, address in enumerate(address_list):
        if i % 30 == 0:
#             if 1 % 120 == 0:
#                 print('Sleeping for 10 seconds to prevent the Request Throttled Error')
#                 time.sleep(10)
            print('Sleeping for 5 seconds to prevent the Request Throttled Error')
            time.sleep(5)
            print('Switching to a new scraper to prevent the Request Throttled Error')
            scraper = cloudscraper.create_scraper()
        fail_count = 0
        error_msg = False
        while True:
            try:
            #     print('Scraping url:', url.format(address))
                page = scraper.get(url.format(address)).text
            #     print('Building beautifulSoup structure...')
                soup = BeautifulSoup(page)
            #     print('Filtering...')
                result = soup.select('h1', {'class': 'h4 mb-0'})
                address_type = result[0].text.split('\n')[2]
                print(f'Address Type: {address_type}, URL: {url.format(address)}')
            except Exception as e:
                print(e)
                fail_count += 1
            if fail_count >= MAX_FAIL_COUNT: # it is a contract address or having failed retrieving for too many times
                type_list.append(False)
                break
            elif address_type == 'Address':
                type_list.append(True)
                break
            elif address_type in ['Contract', 'Token']:
                type_list.append(False)
                break
            else:
                print('Request Throttled Error from the website!')
                print('Sleeping for 10 seconds to prevent the Request Throttled Error')
                time.sleep(10)

    if len(type_list) == 1:
        return type_list[0]
    else:
        return type_list

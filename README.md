Usage:

crawler.py: A crawler library which is capable of crawling address and token transaction data.
address_crawler.py: Calling the crawler module to crawl transaction data by address.
token_crawler.py: Calling the crawler module to crawl transaction data by token. You'll need to manually change the folder name for your own needs.
load_all_explored_nodes_dict.py: An utility script to test whether dictionaries has been stored in correct format.

20200830_crawler.py:
1. Open cmd
2. run "python 20200830_crawler.py --node_count=3 --initial_node=0x0000000000000000000000000000000000000000 --verbose=1"
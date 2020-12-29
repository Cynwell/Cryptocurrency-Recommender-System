import json
from time import sleep

# Get user data from node JS
receive = input()

sleep(2) # For debug purpose

# Tentative API definition 
profile = json.loads(receive)
profile['r1'] = 'Maker'
profile['r1-description'] = 'Maker is a very popular coin'
profile['r1-1d'] = 'Up'
profile['r1-3d'] = 'Down'
profile['r1-7d'] = 'Up'

# Return the data
send = json.dumps(profile)
print(send, end='')

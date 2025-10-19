import requests
import json
import base64    
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

headers = {
    'authority': 'www.oddsportal.com',
    'method': 'GET',
    'scheme': 'https',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'deflate',
    'accept-language': 'en-US,en;q=0.9,fi-FI;q=0.8,fi;q=0.7',
    'content-type': 'application/json',
    'referer': 'https://www.oddsportal.com/',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest'
    }
 
version_id=1
sport_id=1
unique_id='lGmAakqR'
xhash='f6dd57f5645fa984264fdf5c5e951772'

# URL for fetching the data
url = f'https://www.oddsportal.com/match-event/{version_id}-{sport_id}-{unique_id}-1-2-{xhash}.dat?geo=NL&lang=en'

# Send the GET request and retrieve the response text
response = requests.get(url, headers=headers)
data = response.text
print(data)
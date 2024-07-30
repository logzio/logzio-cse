import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
API_KEY = os.getenv('LOGZIO_API_KEY')
BASE_URL = "https://api.logz.io/v1"

# Helper function to make API requests
def make_api_request(endpoint, method='GET', data=None, params=None):
    headers = {
        'X-API-TOKEN': API_KEY,
        'Content-Type': 'application/json'
    }
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, headers=headers, json=data, params=params)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print ("Http Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print ("Something went wrong",err)
    return response.json()
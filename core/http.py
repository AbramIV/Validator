import asyncio
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpClient():
    def __init__(self, timeout=0.1):
        self.code = 0
        self.error = False
        self.message = ""
        self.timeout = timeout
        retry_strategy = Retry(
            total=3,
            status_forcelist=[500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def get(self, url):
        self.reset()
        try:
            response = self.session.get(url, timeout=self.timeout)
            self.code = response.status_code
            self.message = response.text
        except Exception as ex:
            self.error = True
            self.message = str(ex)
            return False
        return True
    
    def reset(self):
        self.code = 0
        self.error = False
        self.message = ""
      
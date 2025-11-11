import asyncio
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpClient():
    def __init__(self):
        self.code = 0
        self.error = False
        self.message = ""
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
            response = self.session.get(url, timeout=1)
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

    async def get_async(self, url):
        self.error = False
        self.message = ""
        self.code = 0
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    self.code = await response.status
                    self.message = await response.text()
        except asyncio.CancelledError:
            print(f"Request to {url} was cancelled.")
            return False
        except aiohttp.ClientError as e:
            print(f"Error fetching {url}: {e}")
            return False
        return True
      
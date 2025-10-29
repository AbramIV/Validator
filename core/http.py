import requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpClient():
    def __init__(self):
        self.response = None
        self.error = False
        self.errorMsg = ""
        retry_strategy = Retry(
            total=1,
            backoff_factor=1,
            #status_forcelist=[500, 502, 503, 504],
        )
        
        adapter  = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def get(self, url):
        self.error = False
        self.errorMsg = ""
        try:
            self.response = self.session.get(url)
            if self.response is None: raise Exception("No response received")
        except Exception as ex:
            self.error = True
            self.errorMsg = str(ex)
            return False
        return True
        


    
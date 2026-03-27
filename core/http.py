import logging
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpClient():
    def __init__(self, timeout=0.1):
        self.requesting = False
        self.completed = False
        self.error = False
        self.message = ""
        self.response = ""
        self.timeout = timeout
        retry_strategy = Retry(
            total=5,
            status_forcelist=[500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
    def get(self, url):
        self.reset()
        self.requesting = True

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            self.response = response.text
            logging.debug(f"HTTP GET RESPONSE {self.response}")
            self.message = ""
        except Exception as ex:
            self.error = True
            self.response = ""
            self.message = str(ex)
        finally:            
            self.requesting = False
            self.completed = True

    def reset(self):
        self.code = 0
        self.error = False
        self.response = ""
        self.message = ""
        self.completed = False

class API1_KEY():
    result = "Result"
    zpl = "Zpl"
    heatsink = "Heatsink"
    pcb1 = "PCB1"
    pcb2 = "PCB2"
    message = "Message"

class API2_KEY():
    result = "Result"
    message = "Message"

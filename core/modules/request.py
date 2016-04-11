import requests
from config import API_URL

class Request(object):
    def __init__(self):
        self.base_url = API_URL

    def get(self, url, params=None, **kwargs):
        print("GET {}".format(self.base_url+url))
        return requests.get(self.base_url + url, params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        return requests.post(self.base_url + url, data, json, **kwargs)


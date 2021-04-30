import datetime
import hashlib
import hmac
import json
import os
import sys
import base64
from urllib.parse import urlencode
from configparser import ConfigParser

import requests

if sys.platform == "win32":
    os.environ.update({"HTTP_PROXY": "socks5h://127.0.0.1:12315"})
    os.environ.update({"HTTPS_PROXY": "socks5h://127.0.0.1:12315"})

conf = ConfigParser()
conf.sections()
conf.read("keys.conf", "utf8")
key_conf=conf["key"]

host = "https://api.hbdm.com"
api_key = key_conf["api_key"]
secret_key = key_conf["secret_key"]

def send_swap_requests(method: str, url: str, **kwargs) -> dict:

    query = {
        "AccessKeyId": api_key,
        "SignatureMethod": "HmacSHA256",
        "SignatureVersion": "2",
        "Timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    }
    query = urlencode(query)
    prepare_sig = method.upper()+"\n"+host[8:]+"\n"+url+"\n"+query
    pre_sig = hmac.new(secret_key.encode("utf8"),
                       prepare_sig.encode("utf8"), 
                       digestmod=hashlib.sha256)
    sig_part = urlencode({"Signature": base64.b64encode(pre_sig.digest()).decode("utf8")})
    query = query+"&"+sig_part
    resp = requests.request(method, host+url+"?"+query, json=kwargs)
    return json.loads(resp.content.decode("utf8"))

def get_current_swap_info(contract_code: str) -> dict:
    method = "post"
    url = "/linear-swap-api/v1/swap_position_info"
    resp = send_swap_requests(method, url, contract_code=contract_code)
    if resp.get("data"):
        return resp["data"][0]
    else:
        return None

def fast_close(contract_code: str, volume: int, direction: str):
    method = "POST"
    url = "/linear-swap-api/v1/swap_lightning_close_position"
    resp = send_swap_requests(method, url, contract_code=contract_code, volume=int(volume), direction=direction)
    return resp

def reverse_direction(direction: str):
    if direction == "buy":
        return "sell"
    elif direction == "sell":
        return "buy"
    else:
        Exception("wha????")

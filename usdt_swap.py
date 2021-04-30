import datetime
import hashlib
import hmac
import json
import os
import sys
import base64
from urllib.parse import urlencode

import requests

if sys.platform == "win32":
    os.environ.update({"HTTP_PROXY": "socks5h://127.0.0.1:12315"})
    os.environ.update({"HTTPS_PROXY": "socks5h://127.0.0.1:12315"})

def send_swap_requests(method: str, url: str, **kwargs) -> dict:

    host = "https://api.hbdm.com"

    query = {
        "AccessKeyId": api_key,
        "SignatureMethod": "HmacSHA256",
        "SignatureVersion": "2",
        "Timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    }
    if kwargs:
        query.update(kwargs)
    query = dict(sorted(query.items()))
    prepare_sig = method.upper()+"\n"+host[8:]+"\n"+url+"\n"+urlencode(query)
    query = urlencode(query)
    pre_sig = hmac.new(secret_key.encode("utf8"),
                       prepare_sig.encode("utf8"), 
                       digestmod=hashlib.sha256)
    sig_part = urlencode({"Signature": base64.b64encode(pre_sig.digest()).decode("utf8")})
    query = query+"&"+sig_part
    resp = requests.request(method, host+url+"?"+query)
    return json.loads(resp.content.decode("utf8"))

def get_current_swap_info(contract_code: str) -> dict:
    url = "/linear-swap-api/v1/swap_position_info"
    method = "post"
    d1=datetime.datetime.now()
    resp = send_swap_requests(method, url, contract_code=contract_code)
    print(datetime.datetime.now()-d1)
    return resp["data"][0]

def fast_close(contract_code: str, volume: float, direction: str):
    method = "POST"
    url = "/linear-swap-api/v1/swap_lightning_close_position"
    resp = send_swap_requests(method, url, contract_code=contract_code, volume=volume, direction=direction)
    return resp

def reverse_direction(direction: str):
    if direction == "buy":
        return "sell"
    elif direction == "sell":
        return "buy"
    else:
        Exception("wha????")

if __name__ == "__main__":
    contract_code = "TRX-USDT"
    result = get_current_swap_info(contract_code)
    resp = fast_close(contract_code, 2, reverse_direction(result["direction"]))
    print(resp)

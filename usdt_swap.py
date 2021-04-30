import datetime
import hashlib
import hmac
import json
import os
import sys
import base64
import pandas as pd
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
    if method.lower() == "get":
        query.update(kwargs)
        query = dict(sorted(query.items()))

    query = urlencode(query)
    prepare_sig = method.upper()+"\n"+host[8:]+"\n"+url+"\n"+query
    pre_sig = hmac.new(secret_key.encode("utf8"),
                       prepare_sig.encode("utf8"), 
                       digestmod=hashlib.sha256)
    sig_part = urlencode({"Signature": base64.b64encode(pre_sig.digest()).decode("utf8")})
    query = query+"&"+sig_part
    if method.lower() == "post":
        resp = requests.request(method, host+url+"?"+query, json=kwargs)
    elif method.lower() == "get":
        resp = requests.request(method, host+url+"?"+query)
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
    # print(resp)
    if resp.get("status") != "ok":
        resp = fast_close(contract_code, volume, direction)
    return resp

def get_kline(contract_code: str, period: str="1min", size: str=1):
    method = "get"
    url = "/linear-swap-ex/market/history/kline"
    resp = send_swap_requests(method, url, contract_code=contract_code, period=period, size=size)
    return resp["data"]

def reverse_direction(direction: str):
    if direction == "buy":
        return "sell"
    elif direction == "sell":
        return "buy"
    else:
        Exception("wha????")

def get_price(contract_code, period="1min", size=1):
    raw_candle_data = get_kline(contract_code, period=period, size=size)
    raw_candle_data = raw_candle_data[::-1]
    final_dict = {"date":[], "high":[], "low":[], "open":[], "close":[], "volume":[]}
    for one_data in raw_candle_data:
        if period == "1day":
            final_dict["date"].append(datetime.datetime.utcfromtimestamp(one_data["id"])+datetime.timedelta(hours=8))
        else:
            final_dict["date"].append(datetime.datetime.utcfromtimestamp(one_data["id"])+datetime.timedelta(hours=8))
        final_dict["high"].append(one_data["high"])
        final_dict["low"].append(one_data["low"])
        final_dict["open"].append(one_data["open"])
        final_dict["close"].append(one_data["close"])
        final_dict["volume"].append(one_data["vol"])
    return  pd.DataFrame(final_dict).set_index("date")

if __name__ == "__main__":
    a=get_price("TRX-USDT")
    print(a)
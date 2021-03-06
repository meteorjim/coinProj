__all__ = ["get_price", "get_mean_line", "custom_data_analyze_func", "get_rate", "get_symbol_list", "draw_candle"]

import datetime
import os
import sys

import numpy as np
import pandas as pd
from huobi.client.generic import GenericClient
from huobi.client.market import MarketClient
from huobi.client.account import AccountClient
from plotly import graph_objects as go


if sys.platform == "win32" or sys.platform == "darwin":
    os.environ.update({"HTTP_PROXY":"socks5h://127.0.0.1:12315"})
    os.environ.update({"HTTPS_PROXY":"socks5h://127.0.0.1:12315"})
    
market_client = MarketClient(url="https://api-aws.huobi.pro")

CLOSE_MEAN_CHANGING_RATE = 0.20
VOLUMES_MEAN_CHANGING_RATE = 3

# def get_account_info():
#     account_client = AccountClient(api_key=g_api_key, secret_key=g_secret_key)

def get_symbol_list(protition=None):
    """
    protition: "main", "innovation", "potentials"
    """
    gc = GenericClient()
    result = gc.get_exchange_symbols()
    if protition:
        return [each_result.symbol for each_result in result if "usdt" in each_result.symbol and each_result.state != "offline" and "3" not in each_result.symbol and each_result.symbol_partition == protition]  
    else :
        return [each_result.symbol for each_result in result if "usdt" in each_result.symbol and each_result.state != "offline" and "3" not in each_result.symbol]

def get_price(symbol, period, size):
    raw_candle_data = market_client.get_candlestick(symbol, period=period, size=size)
    raw_candle_data = raw_candle_data[::-1]
    final_dict = {"date":[], "high":[], "low":[], "open":[], "close":[], "volume":[]}
    for one_data in raw_candle_data:
        if period == "1day":
            final_dict["date"].append(datetime.datetime.utcfromtimestamp(one_data.id)+datetime.timedelta(hours=8))
        else:
            final_dict["date"].append(datetime.datetime.utcfromtimestamp(one_data.id)+datetime.timedelta(hours=8))
        final_dict["high"].append(one_data.high)
        final_dict["low"].append(one_data.low)
        final_dict["open"].append(one_data.open)
        final_dict["close"].append(one_data.close)
        final_dict["volume"].append(one_data.vol)
    return  pd.DataFrame(final_dict).set_index("date")

def get_rate(target_df, types="close"):
    df = target_df.copy()
    df[f"{types}_rate"] = (df[types] - df[types].shift(1)) / df[types].shift(1)
    return df

def draw_candle(df):
    fig=go.Figure(
        data=[
            go.Candlestick(x=df.index, open=df['open'], close=df['close'], high=df['high'], low=df['low']),
            go.Scatter(x=df.index, y=df["mean_5"], name="MA5" ),
            go.Scatter(x=df.index, y=df["mean_13"], name="MA13"),
            go.Scatter(x=df.index, y=df["mean_21"], name="MA21"),
            go.Scatter(x=df.index, y=df["mean_60"], name="MA60"),
            go.Scatter(x=df.index, y=df["mean_120"], name="MA120")
        ], 
        layout={'yaxis': {"fixedrange": False}})
    fig.show()


def get_mean_line(target_df):
    df = target_df.copy()
    df['mean_5'] = df['close'].rolling(5).mean()
    df['mean_13'] = df['close'].rolling(13).mean()
    df['mean_21'] = df['close'].rolling(21).mean()
    df['mean_60'] = df['close'].rolling(60).mean()
    df['mean_120'] = df['close'].rolling(120).mean()
    if len(df["mean_120"].dropna()) > 300:
        df['mean_225'] = df['close'].rolling(225).mean()
    return df


def custom_data_analyze_func(target_df, rolling_days=5):
    """
    ??????????????????dataframe
    Keyword Arguments:
    - target_df {str} -- [????????????] (default: {None})
    - method {str} -- [????????????????????????(vol)/?????????(close)] (default: {'close'})
    - rolling_days {int} -- [????????????????????????] (default: {5})
    """
    result_df = target_df.copy()
    result_df['volume'].replace(0.0,np.nan,inplace=True)
    result_df['close_cr'] = (result_df['close'] - result_df['close'].shift(1)) / result_df['close'].shift(1)
    vol_mean = result_df['volume'].rolling(rolling_days).mean().shift(1)
    result_df[f'volume{rolling_days}_std'] = result_df['volume'].rolling(rolling_days).std()
    result_df['vol_mean{}_cr'.format(rolling_days)] = (result_df['volume'] - vol_mean) / vol_mean
    # result_df = result_df.dropna()
    return result_df

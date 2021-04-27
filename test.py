from time import sleep
from utils import *

symbol = "dogeusdt"
leverage = 50
direction = "buy"
init_win_rates = 20
force_flat = -30

#TODO 获取当前持仓信息
open_point=get_price(symbol, "1min", 1).iloc[-1]["close"]
pr = 0

while True:
    current_point = get_price(symbol, "1min", 1).iloc[-1]["close"]
    if direction == "buy":
        rates = (current_point - open_point)/open_point * 100 * leverage
    elif direction == "sell":
        rates = (open_point - current_point)/open_point * 100 * leverage
    if pr != rates:
        print(f"current rate = {rates}")
    pr = rates
    if rates < force_flat:
        if rates < 0:
            print("I quite QAQ")
        else:
            print(f"I quite XD, and win{abs(current_point-open_point)}, with {rates}%")
        break
    
    if rates > init_win_rates:
        force_flat = init_win_rates - 10
        init_win_rates += 10
    # sleep(0.3)
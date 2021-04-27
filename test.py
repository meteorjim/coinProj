from time import sleep
from utils import *
from plotly import graph_objects as go

symbol = "dogeusdt"
leverage = 30
direction = "buy"
init_win_rates = 20
force_close = -20
change_rate = 10

plot_list = []

#TODO 获取当前持仓信息
open_point=get_price(symbol, "1min", 1).iloc[-1]["close"]
pr = 0

while True:
    current_point = get_price(symbol, "1min", 1).iloc[-1]["close"]
    if direction == "buy":
        rates = (current_point - open_point)/open_point * 100 * leverage
    elif direction == "sell":
        rates = (open_point - current_point)/open_point * 100 * leverage
    else:
        raise Exception("wha???????")
    if pr != rates:
        print("current rate = {:.4f}%".format(rates))
        plot_list.append(rates)
    pr = rates
    if rates < force_close:
        if rates < 0:
            print("I quite QAQ")
        else:
            print(f"I quite XD, with {rates}%")
        break
    
    if rates > init_win_rates:
        force_close = init_win_rates - change_rate
        init_win_rates += change_rate

fig = go.Figure(
    go.Scatter(y=plot_list)
)
fig.show()
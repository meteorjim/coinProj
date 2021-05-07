import datetime

import numpy as np



# 策略2 5均线>13均>21>60均 且均线间的差值逐渐扩大
def strategy2(target_df, is_strict=True):
    df = target_df.copy()
    df['delta5to13'] = df['mean_5']-df['mean_13']
    df['delta13to21'] = df['mean_13']-df['mean_21']
    df['delta21to60'] = df['mean_21']-df['mean_60']
    try:
        if df['mean_5'][-1] > df['mean_13'][-1] > df['mean_21'][-1] > df['mean_60'][-1] :
            if df['delta5to13'][-1] > df['delta5to13'][-2] and df['delta13to21'][-1] > df['delta13to21'][-2] and df['delta21to60'][-1] > df['delta21to60'][-2]:
                if is_strict and df['delta5to13'][-2] < df['delta5to13'][-3] or df['delta13to21'][-2] < df['delta13to21'][-3] or df['delta21to60'][-2] < df['delta21to60'][-3]:
                    return True
                elif is_strict:
                    return False
                return True
        else:
            return False
    except Exception as ex:
        raise Exception("s2"+ex)
        return False

# 策略3 最近一个月的最后收盘价对比月初开盘价上涨30%以上，前一个月上涨幅度在0-30%之间，前2个月上涨幅度在0-30%之间
def strategy3(df, start_month):
    month_data = df.groupby('month')
    last_month = start_month - 1
    if last_month < 1 :
        last_month = last_month+12
    two_month_before = last_month -1 
    if two_month_before < 1 :
        two_month_before = two_month_before+12
    try:
        up_rate = (month_data.last()['close'][start_month] - month_data.first()['open'][start_month])/month_data.first()['open'][start_month]

        if 0 < up_rate < 0.33:
            last_up_rate = (month_data.last()['close'][last_month] - month_data.first()['open'][last_month])/month_data.first()['open'][last_month]

            if 0 < last_up_rate < 0.33:
                two_month_up_rate = (month_data.last()['close'][two_month_before] - month_data.first()['open'][two_month_before])/month_data.first()['open'][two_month_before]

                if 0 < two_month_up_rate < 0.33:
                    return True
        return False
    except Exception as ex:
        print("s3", ex)
        raise ex+'输入月份有误'

# 策略4 当天的开盘价+收盘价均高于全部均线 且 前一天均线没有高于全部均线 且 5均>13>21
def get_longterm_mean_df(target_df, target_day=datetime.datetime.now().date()):
    df = target_df.copy()
    df['volume'].replace(0.0,np.nan,inplace=True)
    df=df.dropna()
    df['hc1']=df['close'].shift(1)
    df['c1'] = ((df['close']>df['mean_5'])   & (df['open']>df['mean_5'])   &
                (df['close']>df['mean_13'])  & (df['open']>df['mean_13'])  & 
                (df['close']>df['mean_21'])  & (df['open']>df['mean_21'])  & 
                (df['close']>df['mean_60'])  & (df['open']>df['mean_60'])  & 
                (df['close']>df['mean_120']) & (df['open']>df['mean_120']) &
                (df['close']>df['mean_225']) & (df['open']>df['mean_225']))
    S_T = df['c1'].shift(1).astype(bool)
    df['c2'] = ~S_T.dropna()
    df['c3'] = (df['mean_5'] > df['mean_13']) &  (df['mean_13']>df['mean_21'])  
    df.dropna(inplace=True)
    if len(df)>0:
        tt = df[df['c1'] & df['c2'] & df['c3']]
        if len(tt)>0 and target_day in tt.index.strftime("%Y-%m-%d").tolist():
            return True
        else:
            return False
    else:
        raise Exception("has no proper data")

        
# 策略5 快均线依次突破慢线，且最小的快均线与最大慢线的差距 小于 0.3%
def mean_line_breakthrough(target, window_size=15):
    fast_line_content = ['mean_5','mean_13','mean_21']
    slow_line_content = ['mean_60','mean_120','mean_225']
    if len(target)>window_size:
        raise Exception('size is too large')
    fast_line=target[fast_line_content]
    slow_line=target[slow_line_content]
    # 窗口初始时间快线至少小于一根慢线
    if ~np.all(fast_line.iloc[0] < slow_line.iloc[0].max()):
        return False
    # 窗口最后时间最小的一根快线与最大的一根慢线的差值小于 3%
    if ~(abs(fast_line.iloc[-1].min() - slow_line.iloc[-1].max())/slow_line.iloc[-1].max() < 0.003):
        return False
    # 全部快线在窗口内保持增长
    if ~np.all(fast_line.iloc[-1] - fast_line.iloc[0]>0):
        return False
    # 定义三个trigger，1、全部快线均小于最大慢线，2、m5大于最大慢线，m13,m21小于。3、m5, m13大于最大慢线，m21小于
    # 三个trigger必须依次实现
    t_all_fast = False
    t_m5 = False
    t_m5_m13 = False
    for i in range(len(target)):
        if t_all_fast == False and t_m5 == False and t_m5_m13 == False:
            if np.all(target.iloc[i][fast_line_content] < target.iloc[i][slow_line_content].max()):
                t_all_fast = True
        elif t_all_fast == True and t_m5 == False and t_m5_m13 == False:
            if target.iloc[i]['mean_5'] > target.iloc[i][slow_line_content].max():
                t_m5 = True
        elif t_all_fast == True and t_m5 == True and t_m5_m13 == False:
            if np.all(target.iloc[i][['mean_5','mean_13']] > target.iloc[i][slow_line_content].max()):
                t_m5_m13 = True
    if t_all_fast and t_m5 and t_m5_m13:
        return True
    else :
        return False

# 策略8 当天收盘价高于快均线，且开盘价低于快均线。
def all_mean_break(df, target_date = -1):
    return df.iloc[target_date]['open'] < df.iloc[target_date]['mean_5'] and df.iloc[target_date]['open'] < df.iloc[target_date]['mean_13'] and df.iloc[target_date]['open'] < df.iloc[target_date]['mean_21'] and df.iloc[target_date]['close'] > df.iloc[target_date]['mean_5'] and df.iloc[target_date]['close'] > df.iloc[target_date]['mean_13'] and df.iloc[target_date]['close'] > df.iloc[target_date]['mean_21']
    
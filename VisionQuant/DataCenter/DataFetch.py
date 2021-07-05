import baostock as bs
import numpy as np
import pandas as pd
from VisionQuant.utils import TimeTool
from mootdx.quotes import Quotes
from mootdx.reader import Reader


def mergeKdata(kdata, period, new_period):
    interval = int(int(new_period) / int(period))
    count = 0
    data_list = []
    while count < len(kdata):
        tmp_data = kdata[count:count + interval]
        tmp_high = tmp_data['high'].max()
        tmp_low = tmp_data['low'].min()
        tmp_open = tmp_data['open'].iloc[0]
        tmp_close = tmp_data['close'].iloc[len(tmp_data['close']) - 1]
        tmp_amount = tmp_data['amount'].sum()
        tmp_volume = tmp_data['volume'].sum()
        tmp_time = tmp_data['time'].iloc[len(tmp_data['time']) - 1]
        data_list.append((tmp_open, tmp_high, tmp_low, tmp_close, tmp_volume, tmp_amount, tmp_time))
        count = count + interval
    new_out_df = pd.DataFrame(data_list, columns=['open', 'high', 'low', 'close', 'volume', 'amount', 'time'])
    return new_out_df


def fetch_kdata_from_tdx(code, frequency, start_time=None, end_time=None, **kwargs):
    tdx_path = 'D:/Program/new_tdx'
    reader = Reader.factory(market='std', tdxdir=tdx_path)
    if start_time is None:
        start_time = TimeTool.str_to_npdt64('2019-1-1 9:30')
    if end_time is None:
        end_time = TimeTool.get_now_time()
    if frequency == 'd':
        # 读取日线数据
        out_df = reader.daily(symbol=code)
        out_df['time'] = out_df.index.values
        if out_df['volume'].iloc[-47] == 0 and out_df['volume'].iloc[-2] == 0:
            out_df = out_df[:-48]  # 去除停牌数据
        out_df = out_df[(out_df['time'] >= start_time) & (out_df['time'] <= end_time)]
        out_df = out_df.reset_index(drop=True)
    elif frequency == '5':
        # 读取5分钟数据
        out_df = reader.fzline(symbol=code)  # 约0.2s
        out_df['time'] = out_df.index.values
        out_df = out_df[(out_df['time'] >= start_time) & (out_df['time'] <= end_time)]
        if out_df['volume'].iat[-47] == 0 and out_df['volume'].iat[-2] == 0:
            out_df = out_df[:-48]  # 去除停牌数据
        out_df = out_df.reset_index(drop=True)
    elif frequency == '1':
        # 读取1分钟数据
        out_df = reader.minute(symbol=code)
        out_df['time'] = out_df.index.values
        if out_df['volume'].iloc[-47] == 0 and out_df['volume'].iloc[-2] == 0:
            out_df = out_df[:-48]  # 去除停牌数据
        out_df = out_df[(out_df['time'] >= start_time) & (out_df['time'] <= end_time)]
        out_df = out_df.reset_index(drop=True)
    elif frequency in ['15', '30', '60', '120']:
        # 读取5分钟数据
        out_df = reader.fzline(symbol=code)
        out_df['time'] = out_df.index.values
        if out_df['volume'].iloc[-47] == 0 and out_df['volume'].iloc[-2] == 0:
            out_df = out_df[:-48]  # 去除停牌数据
        out_df = out_df[(out_df['time'] >= start_time) & (out_df['time'] <= end_time)]
        out_df = out_df.reset_index(drop=True)
        out_df = mergeKdata(out_df, '5', frequency)
    else:
        raise ValueError
    return out_df


# todo: 修改参数逻辑
def fetch_kdata_from_tdx_live(code, frequency, start_time=None, end_time=None, **kwargs):
    if end_time is None:
        end_time = TimeTool.get_now_time()
    if start_time is None:
        start_time = TimeTool.time_standardization('2020-2-1')
    client = Quotes.factory(market='std')
    fetched_kdata = client.bars(symbol=code, frequency='0', offset='400')
    fetched_kdata['time'] = fetched_kdata['datetime'].apply(lambda x: TimeTool.str_to_dt(x))
    fetched_kdata['volume'] = fetched_kdata['vol']
    new_kdata = fetched_kdata[['open', 'close', 'high', 'low', 'volume', 'amount', 'time']]
    return new_kdata


def fetch_kdata(code, frequency, method_func, start_time=None, end_time=None, **kwargs):
    df = method_func(code=code,
                     frequency=frequency,
                     start_time=start_time,
                     end_time=end_time,
                     kwargs=kwargs)
    return df


if __name__ == '__main__':
    VQtdx = fetch_kdata_from_tdx
    test_code = '600639'
    test_frequency = '5'
    test_start_time = '2020-2-1'
    # test_end_time = '2021-06-25 15:00:00'
    test_df = fetch_kdata(code=test_code,
                          frequency=test_frequency,
                          method_func=VQtdx,
                          start_time=test_start_time,
                          end_time=None)
    print(test_df)

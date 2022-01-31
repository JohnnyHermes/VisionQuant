import datetime
import numpy as np
import re
from path import Path

from VisionQuant.utils.Params import Stock, LOCAL_DIR

# 交易日历读取
tradedate_fpath = Path('/'.join([LOCAL_DIR, 'AshareTradeDate.txt']))
if tradedate_fpath.exists():
    with open(tradedate_fpath, 'r') as f:
        data = f.read()
        ASHARE_TRADE_DATE = data.split(',')
else:
    ASHARE_TRADE_DATE = None


def dt_to_npdt64(dt):
    return np.datetime64(dt)


def npdt64_to_dt(dt64):
    dt = dt64.astype(datetime.datetime)
    if isinstance(dt, datetime.datetime):
        return dt
    elif isinstance(dt, int):
        return datetime.datetime.utcfromtimestamp(dt * 1e-9)

    # return (dt64 - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')


def str_to_dt(strtime):
    if re.match(r'\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    elif re.match(r'\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d %H:%M')
        t = t.replace(second=0)
    elif re.match(r'\d{14}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y%m%d%H%M%S')
    elif re.match(r'\d{2,4}-\d{1,2}-\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d')
        t = t.replace(hour=9, minute=0, second=0)
    else:
        raise ValueError
    return t


def str_to_npdt64(strtime):
    t = str_to_dt(strtime)
    return dt_to_npdt64(t)


def dt_to_str(dt, fmt='%Y-%m-%d %H:%M:%S'):
    return dt.strftime(fmt)


def npdt64_to_str(dt64, fmt='%Y-%m-%d %H:%M:%S'):
    dt = npdt64_to_dt(dt64)  # np.dt64 转 datetime.datetime
    return dt_to_str(dt, fmt)


def time_to_str(t, fmt='%Y-%m-%d %H:%M:%S'):
    if isinstance(t, datetime.datetime):
        return dt_to_str(t, fmt)
    elif isinstance(t, np.datetime64):
        return npdt64_to_str(t, fmt)
    elif isinstance(t, str):
        return t
    else:
        raise ValueError("Wrong Time")


def time_standardization(t):
    if isinstance(t, datetime.datetime):
        return dt_to_npdt64(t)
    elif isinstance(t, str):
        return str_to_npdt64(t)
    elif isinstance(t, int):
        return str_to_npdt64(str(t))
    elif isinstance(t, np.datetime64):
        return t
    else:
        raise ValueError("Wrong Time")


def get_now_time(return_type: str = 'npdt64'):
    """

    :param return_type: 支持三种类型 'datetime':datetime.datetime
                                   'npdt64':np.datetime64
                                   'str':str
    :return:
    """
    if return_type == 'datetime':
        return datetime.datetime.now()
    elif return_type == 'str':
        return dt_to_str(datetime.datetime.now())
    elif return_type == 'npdt64':
        return dt_to_npdt64(datetime.datetime.now())

    else:
        raise ValueError


def is_trade_time(market):
    nowtime = get_now_time(return_type='datetime')
    weekday = nowtime.isoweekday()
    if Stock.is_ashare(market):
        if weekday > 5:
            return 0
        if ASHARE_TRADE_DATE is not None:
            date_str = time_to_str(nowtime, '%Y-%m-%d')
            if date_str not in ASHARE_TRADE_DATE:
                return 0
        t1 = nowtime.replace(hour=9, minute=30, second=0)
        t2 = nowtime.replace(hour=11, minute=30, second=15)
        t3 = nowtime.replace(hour=13, minute=0, second=0)
        t4 = nowtime.replace(hour=15, minute=0, second=15)
        if t1 <= nowtime <= t2 or t3 <= nowtime <= t4:
            return 1
        else:
            return 0
    else:
        return 0


def time_delta(t1, t2):
    if isinstance(t1, datetime.datetime):
        t1 = dt_to_npdt64(t1)
    elif isinstance(t1, str):
        t1 = str_to_npdt64(t1)
    if isinstance(t2, datetime.datetime):
        t2 = dt_to_npdt64(t2)
    elif isinstance(t2, str):
        t2 = str_to_npdt64(t2)
    return (t2 - t1) / np.timedelta64(1, 's')


if __name__ == '__main__':
    test_strtime = '2021-06-27 9:0:0'
    test_dt = str_to_dt(test_strtime)
    test_npdt64 = dt_to_npdt64(test_dt)
    new_test_dt = npdt64_to_dt(test_npdt64)
    print(npdt64_to_str(test_npdt64))
    print(test_dt, new_test_dt)
    print(test_npdt64, type(test_npdt64), new_test_dt)
    # print(str_to_dt(test_strtime), type(str_to_dt(test_strtime)))
    print(is_trade_time(Stock.Ashare.MarketSH.ETF))

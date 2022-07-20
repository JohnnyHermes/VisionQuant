import datetime
import numpy as np
import re
from path import Path

from VisionQuant.utils.Params import MarketType, LOCAL_DIR, Freq

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
    if t is None:
        return None
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


def generate_future_time_list(market, freq, last_time):
    if MarketType.is_ashare(market):
        nearest_trade_date = get_nearest_trade_date(last_time, MarketType.Ashare, 'end')
        future_trade_dates = tuple(filter(lambda x: x >= nearest_trade_date, ASHARE_TRADE_DATE))
        minute_str_list = []
        if freq == Freq.MIN1:
            hours = (9, 10, 11, 13, 14, 15)
            for hour in hours:
                if hour == 9:
                    minute_str_list += ['{:0>2}:{:0>2}'.format(hour, minute) for minute in range(31, 60)]
                elif hour == 11:
                    minute_str_list += ['{:0>2}:{:0>2}'.format(hour, minute) for minute in range(0, 31)]
                elif hour == 13:
                    minute_str_list += ['{:0>2}:{:0>2}'.format(hour, minute) for minute in range(1, 60)]
                elif hour == 15:
                    minute_str_list.append('15:00')
                else:
                    minute_str_list += ['{:0>2}:{:0>2}'.format(hour, minute) for minute in range(0, 60)]
        future_time_list = []
        for trade_date in future_trade_dates:
            future_time_list += ['{}\n{}'.format(trade_date, minute_str) for minute_str in minute_str_list]
        return future_time_list
    else:  # todo: 支持更多市场类型
        raise ValueError("错误的市场类型")


def get_nearest_trade_date(t, market, flag='end'):
    """
    如果是end，那么盘中得到的日期将是当日，如果是start，那么是下一个交易日
    """

    def _get_nearest_trade_date(_t, _trade_date_list, _flag='end'):
        if _flag == 'end':
            i = len(_trade_date_list) - 1
            while i >= 0:
                if _t >= _trade_date_list[i]:
                    return _trade_date_list[i]
                else:
                    i -= 1
            return _trade_date_list[0]
        elif _flag == 'start':
            i = 0
            len_list = len(_trade_date_list)
            while i <= len_list - 1:
                print(_trade_date_list[i])
                if _t < _trade_date_list[i]:
                    return _trade_date_list[i]
                else:
                    i += 1
            return _trade_date_list[len(_trade_date_list) - 1]

    if MarketType.is_ashare(market):
        if ASHARE_TRADE_DATE is None:
            return None
        date_str = time_to_str(t, fmt="%Y-%m-%d")
        return _get_nearest_trade_date(date_str, ASHARE_TRADE_DATE, flag)
    elif MarketType.is_future(market):
        if ASHARE_TRADE_DATE is None:
            return None
        date_str = time_to_str(t, fmt="%Y-%m-%d")
        if 21 <= get_now_time(return_type='datetime').hour <= 23:
            return _get_nearest_trade_date(date_str, ASHARE_TRADE_DATE, 'start')
        else:
            return _get_nearest_trade_date(date_str, ASHARE_TRADE_DATE, flag)
    else:
        raise ValueError  # todo: 不同市场类别


def is_trade_time(market):
    nowtime = get_now_time(return_type='datetime')
    weekday = nowtime.isoweekday()
    if MarketType.is_ashare(market):
        if weekday > 5:
            return 0
        if ASHARE_TRADE_DATE is not None:
            date_str = time_to_str(nowtime, '%Y-%m-%d')
            if date_str not in ASHARE_TRADE_DATE:
                return 0
        t1 = nowtime.replace(hour=9, minute=30, second=0, microsecond=0)
        # t2 = nowtime.replace(hour=11, minute=30, second=15)
        # t3 = nowtime.replace(hour=13, minute=0, second=0)
        t4 = nowtime.replace(hour=15, minute=30, second=0, microsecond=0)
        # if t1 <= nowtime <= t2 or t3 <= nowtime <= t4:
        if t1 <= nowtime <= t4:
            return 1
        else:
            return 0
    elif MarketType.is_future(market):
        if weekday > 5:
            return 0
        if ASHARE_TRADE_DATE is not None:
            date_str = time_to_str(nowtime, '%Y-%m-%d')
            if date_str not in ASHARE_TRADE_DATE:
                return 0
            h = nowtime.hour
            if 0 <= h <= 3 or 9 <= h <= 16 or 21 <= h <= 23:
                return 1
            else:
                return 0
    else:
        return 0


def is_trade_date(market):
    nowtime = get_now_time(return_type='datetime')
    weekday = nowtime.isoweekday()
    if MarketType.is_ashare(market):
        if weekday > 5:
            return 0
        if ASHARE_TRADE_DATE is not None:
            date_str = time_to_str(nowtime, '%Y-%m-%d')
            if date_str not in ASHARE_TRADE_DATE:
                return 0
        return 1
    elif MarketType.is_future(market):
        return 0


def get_start_time(end_time, **kwargs):
    if isinstance(end_time, str):
        end_time = str_to_dt(end_time)
    elif isinstance(end_time, np.datetime64):
        end_time = npdt64_to_dt(end_time)
    start_time = time_minus(end_time, standardization=False, **kwargs)
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return dt_to_npdt64(start_time)


def time_plus(t, standardization=True, **kwargs):
    if isinstance(t, str):
        t = str_to_dt(t)
    elif isinstance(t, np.datetime64):
        t = npdt64_to_dt(t)
    new_t = t + datetime.timedelta(**kwargs)
    if standardization:
        return time_standardization(new_t)
    else:
        return new_t


def time_minus(t, standardization=True, **kwargs):
    if isinstance(t, str):
        t = str_to_dt(t)
    elif isinstance(t, np.datetime64):
        t = npdt64_to_dt(t)
    new_t = t - datetime.timedelta(**kwargs)
    if standardization:
        return time_standardization(new_t)
    else:
        return new_t


def replace_time(t, **kwargs):
    if isinstance(t, str):
        t = str_to_dt(t)
    elif isinstance(t, np.datetime64):
        t = npdt64_to_dt(t)
    res = t.replace(**kwargs)
    return dt_to_npdt64(res)


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
    print(is_ashare_trade_time(MarketType.Ashare.SH.ETF))

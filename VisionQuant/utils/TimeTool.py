import datetime
import numpy as np
import re


def dt_to_npdt64(dt):
    return np.datetime64(dt)


def str_to_dt(strtime):
    if re.match(r'\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S')
    elif re.match(r'\d{2,4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d %H:%M')
    elif re.match(r'\d{2,4}-\d{1,2}-\d{1,2}', strtime):
        t = datetime.datetime.strptime(strtime, '%Y-%m-%d')
        t = t.replace(hour=9, minute=30)
    else:
        raise ValueError
    return t


def str_to_npdt64(strtime):
    t = str_to_dt(strtime)
    return dt_to_npdt64(t)


def dt_to_str(dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def time_standardization(t):
    if isinstance(t, datetime.datetime):
        return dt_to_npdt64(t)
    elif isinstance(t, str):
        return str_to_npdt64(t)
    elif isinstance(t, np.datetime64):
        return t
    else:
        raise ValueError("Wrong Time")


def get_now_time(return_type='npdt64'):
    if return_type == 'datetime':
        return datetime.datetime.now()
    elif return_type == 'str':
        return dt_to_str(datetime.datetime.now())
    elif return_type == 'npdt64':
        return dt_to_npdt64(datetime.datetime.now())

    else:
        raise ValueError


def is_trade_time(market):
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
    test_strtime = '2021-06-27'
    print(str_to_dt(test_strtime), type(str_to_dt(test_strtime)))

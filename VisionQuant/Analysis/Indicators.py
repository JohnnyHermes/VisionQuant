import talib as ta


def Vprice(_open, _close, _high, _low):
    return ta.AVGPRICE(_open, _high, _low, _close)


def MA(stk_datas, period):
    return ta.MA(stk_datas, timeperiod=period, matype=0)


def EMA(stk_datas, period):
    # ema = np.full(len(stk_datas), np.nan, dtype=np.float32)
    # ema[period - 2] = np.mean(stk_datas[:period - 1])
    # for i in range(period - 1, len(stk_datas)):
    #     ema[i] = 2.0 / (period + 1) * (stk_datas[i] - ema[i - 1]) + ema[i - 1]
    ema = ta.EMA(stk_datas, period)
    return ema


def MACD(stk_datas, short_period=9, long_period=26, signalperiod=9):
    diff, dea, macd = ta.MACD(stk_datas, fastperiod=short_period, slowperiod=long_period,
                              signalperiod=signalperiod)
    return diff, dea, macd


def Trend(data, method='EMA'):
    if method == 'EMA':
        MA0 = EMA(period=3 * 48, stk_datas=data)
        MA1 = EMA(period=9 * 48, stk_datas=data)
        MA2 = EMA(period=14 * 48, stk_datas=data)
        MA3 = EMA(period=28 * 48, stk_datas=data)
        MA4 = EMA(period=60 * 48, stk_datas=data)
        MA5 = EMA(period=120 * 48, stk_datas=data)
    else:
        MA0 = MA(period=3 * 48, stk_datas=data)
        MA1 = MA(period=9 * 48, stk_datas=data)
        MA2 = MA(period=14 * 48, stk_datas=data)
        MA3 = MA(period=28 * 48, stk_datas=data)
        MA4 = MA(period=60 * 48, stk_datas=data)
        MA5 = MA(period=120 * 48, stk_datas=data)
    short = MA0 * 0.07 + MA1 * 0.21 + MA2 * 0.36 + MA3 * 0.36
    mid = MA2 * 0.19 + MA3 * 0.31 + MA4 * 0.5
    long = MA3 * 0.19 + MA4 * 0.31 + MA5 * 0.5
    return short, mid, long

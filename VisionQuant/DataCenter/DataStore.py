import pandas as pd
from path import Path
from tables.exceptions import HDF5ExtError
from VisionQuant.utils.Params import LOCAL_DIR, HDF5_COMP_LEVEL, HDF5_COMPLIB, Stock


def _hdf5_market_transform(_market):
    if _market in [Stock.Ashare.MarketSH, Stock.Ashare.MarketSH.STOCK, Stock.Ashare.MarketSH.ETF,
                   Stock.Ashare.MarketSH.INDEX, Stock.Ashare.MarketSH.KCB]:
        return 'Ashare', 'sh'
    elif _market in [Stock.Ashare.MarketSZ, Stock.Ashare.MarketSZ.STOCK, Stock.Ashare.MarketSZ.ETF,
                     Stock.Ashare.MarketSZ.INDEX, Stock.Ashare.MarketSZ.CYB]:
        return 'Ashare', 'sz'
    else:
        raise ValueError("错误的市场类型")


def store_kdata_to_hdf5(datastruct):
    try:
        market, market_type = _hdf5_market_transform(datastruct.code.market)
        if market_type is None:
            fname = datastruct.code.code + '.h5'
        else:
            fname = market_type + datastruct.code.code + '.h5'
        fpath = Path('/'.join([LOCAL_DIR, 'KData', market, fname]))
        store = pd.HDFStore(fpath, complib=HDF5_COMPLIB, complevel=HDF5_COMP_LEVEL)
    except HDF5ExtError as e:
        print(e)
    else:
        for freq in datastruct.get_freqs():
            kdata = datastruct.get_kdata(freq)
            if len(kdata) > 0:
                store.put(key='_' + freq, value=kdata.data)
        store.close()


def store_code_list_stock(list_df, market):
    def market_transform(_market):
        if _market is Stock.Ashare:
            return 'ashare'
        else:  # todo:增加不同市场类型
            return 'future'

    market_str = market_transform(market)
    fpath = Path('/'.join([LOCAL_DIR, 'code_list_' + market_str + '.csv']))
    list_df.to_csv(fpath, encoding='utf-8', index=False)

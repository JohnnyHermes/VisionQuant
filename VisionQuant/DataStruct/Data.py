import pandas as pd

from VisionQuant.utils import TimeTool
from copy import deepcopy
from pandas import concat
from functools import lru_cache

from VisionQuant.utils.Params import Freq


class KDataStruct:
    def __init__(self, kdata_df, columns=None):
        if columns is None:
            columns = ['time', 'open', 'close', 'high', 'low', 'volume', 'amount']
        if len(kdata_df) == 0 or kdata_df is None:
            self.data = pd.DataFrame(columns=columns)
        else:
            self.data = kdata_df

    @lru_cache()
    def __len__(self):
        return len(self.data)

    def filter(self, key='index', start=0, end=-1, is_reset_index=False):
        if len(self) == 0:
            return self
        if key == 'index':
            if start < 0:
                start = len(self) + start
            if end < 0:
                end = len(self) + end
            out_df = self.data[(self.data.index >= start) & (self.data.index <= end)]
        elif key in self.data.columns:
            if key == 'time':
                if start != 0 and end != -1:
                    start = TimeTool.time_standardization(start)
                    end = TimeTool.time_standardization(end)
                    out_df = self.data[(self.data[key] >= start) & (self.data[key] <= end)]
                elif start == 0 and end != -1:
                    end = TimeTool.time_standardization(end)
                    out_df = self.data[self.data[key] <= end]
                elif start != 0 and end == -1:
                    start = TimeTool.time_standardization(start)
                    out_df = self.data[self.data[key] >= start]
                else:
                    out_df = self.data
            else:
                out_df = self.data
        else:
            raise ValueError
        if is_reset_index:
            out_df = out_df.reset_index(drop=True)
        new_KDataStruct = KDataStruct(out_df)
        return new_KDataStruct

    @lru_cache()
    def get_last_bar(self):
        if len(self) == 0:
            return None
        return self.data.tail(1)

    @lru_cache()
    def get_first_bar(self):
        if len(self) == 0:
            return None
        return self.data.head(1)

    @lru_cache()
    def get_last_time(self):
        line = self.get_last_bar()
        if line is not None:
            return TimeTool.time_standardization(line.time.values[0])
        else:
            return None

    @lru_cache()
    def get_start_time(self):
        line = self.get_first_bar()
        if line is not None:
            return TimeTool.time_standardization(line.time.values[0])
        else:
            return None

    @lru_cache()
    def get_last_index(self):
        line = self.get_last_bar()
        if line is not None:
            return line.index.values[0]
        else:
            return None

    @lru_cache()
    def get_last_price(self):
        line = self.get_last_bar()
        if line is not None:
            return line.close.values[0]
        else:
            return None

    @lru_cache()
    def get_last_bar_values(self):
        line = self.get_last_bar()
        if line is not None:
            return line.open.values[0], line.close.values[0], line.high.values[0], \
                   line.low.values[0], line.volume.values[0]
        else:
            return None

    def remove_zero_volume(self):
        # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
        self.data.drop(self.data[self.data['amount'] < 0.001].index, inplace=True)
        self.data.reset_index(drop=True, inplace=True)

    @lru_cache(maxsize=128)
    def convert_index_time(self, index=None, time=None):
        if len(self) == 0:
            print('数据为空')
            return 0
        if index is not None:
            return TimeTool.time_standardization(self.data[self.data.index == index].time.values[0])
        elif time is not None:
            return self.data[self.data.time == TimeTool.time_standardization(time)].index.values[0]

    def update(self, new_kdata):
        if len(new_kdata) == 0:
            return self
        if len(self) > 0:
            tmp_ori_data = self.data[self.data['time'] < new_kdata['time'].values[0]]
            self.data = concat([tmp_ori_data, new_kdata])
            self.data = self.data.reset_index(drop=True)
        else:
            self.data = new_kdata
            self.data = self.data.reset_index(drop=True)

        self.__len__.cache_clear()
        self.get_last_bar.cache_clear()
        self.get_last_index.cache_clear()
        self.get_last_bar_values.cache_clear()
        self.get_last_time.cache_clear()
        self.get_last_price.cache_clear()
        return self

    def repair(self, new_kdata):
        if len(new_kdata) == 0:
            return self
        tmp_ori_data = self.data[self.data['time'] > new_kdata['time'].values[len(new_kdata['time']) - 1]]
        self.data = concat([new_kdata, tmp_ori_data])
        self.__len__.cache_clear()
        self.get_first_bar.cache_clear()
        self.get_start_time.cache_clear()
        return self


class BaseDataStruct:
    def __init__(self, code: object, kdata_dict, columns=None):
        self.code = code
        self.kdata = dict()
        for frequency, kdata_df in kdata_dict.items():
            self.kdata[frequency] = KDataStruct(kdata_df, columns)

    def get_kdata(self, frequency):
        return self.kdata[frequency]

    def add_kdata(self, kdata_dict):
        for frequency, kdata_df in kdata_dict.items():
            self.kdata[frequency] = KDataStruct(kdata_df)

    def get_freqs(self):
        return self.kdata.keys()

    def get_last_time(self, freqs):
        availavle_freqs = self.get_freqs()
        if isinstance(freqs, list):
            res = dict()
            for freq in freqs:
                if freq in availavle_freqs:
                    res[freq] = self.kdata[freq].get_last_time()
                else:
                    raise ValueError('DataStruct中不含该周期的数据')
            return res
        else:
            if freqs in availavle_freqs:
                return self.kdata[freqs].get_last_time()
            else:
                raise ValueError('DataStruct中不含该周期的数据')

    def get_start_time(self, freqs):
        availavle_freqs = self.get_freqs()
        if isinstance(freqs, list):
            res = dict()
            for freq in freqs:
                if freq in availavle_freqs:
                    res[freq] = self.kdata[freq].get_start_time()
                else:
                    raise ValueError('DataStruct中不含该周期的数据')
            return res
        else:
            if freqs in availavle_freqs:
                return self.kdata[freqs].get_start_time()
            else:
                raise ValueError('DataStruct中不含该周期的数据')

    def filter(self, key='index', start=0, end=-1, is_reset_index=True, freqs=None):
        if freqs is not None and not isinstance(freqs,list):
            freqs = [freqs]
        tmp_data = self.copy()

        for freq, kdata in tmp_data.kdata.items():
            tmp_data.kdata[freq] = kdata.filter(key=key, start=start, end=end, is_reset_index=is_reset_index)
        if freqs is not None:
            del_freqs = []
            for freq, kdata in tmp_data.kdata.items():
                if freq not in freqs:
                    del_freqs.append(freq)
            for freq in del_freqs:
                del tmp_data.kdata[freq]
        return tmp_data

    def remove_zero_volume(self):
        for freq, kdata in self.kdata.items():
            # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
            self.kdata[freq].remove_zero_volume()

    def copy(self):
        return deepcopy(self)

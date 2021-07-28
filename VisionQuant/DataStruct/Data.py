from VisionQuant.utils import TimeTool
from numpy import datetime64
from datetime import datetime
from pandas import concat


class KDataStruct:
    def __init__(self, kdata_df):
        self.data = kdata_df

    def __len__(self):
        return len(self.data)

    def fliter(self, key='index', start=0, end=-1, is_reset_index=False):
        if key == 'index':
            if start < 0:
                start = len(self) + start
            if end < 0:
                end = len(self) + end
            out_df = self.data[(self.data.index >= start) & (self.data.index <= end)]
        elif key in self.data.columns:
            if key == 'time':
                start = TimeTool.time_standardization(start)
                end = TimeTool.time_standardization(end)
            out_df = self.data[(self.data[key] >= start) & (self.data[key] <= end)]
        else:
            raise ValueError
        if is_reset_index:
            out_df = out_df.reset_index(drop=True)
        new_KDataStruct = KDataStruct(out_df)
        return new_KDataStruct

    def get_last_bar(self):
        return self.data.tail(1)

    def get_first_bar(self):
        return self.data.head(1)

    def get_last_time(self):
        line = self.get_last_bar()
        return TimeTool.time_standardization(line.time.values[0])

    def get_start_time(self):
        line = self.get_first_bar()
        return TimeTool.time_standardization(line.time.values[0])

    def get_last_index(self):
        line = self.get_last_bar()
        return line.index.values[0]

    def get_last_price(self):
        line = self.get_last_bar()
        return line.close.values[0]

    def convert_index_time(self, index=None, time=None):
        if index is not None:
            return TimeTool.time_standardization(self.data[self.data.index == index].time.values[0])
        elif time is not None:
            return self.data[self.data.time == TimeTool.time_standardization(time)].index.values[0]

    def update(self, new_kdata):
        tmp_ori_data = self.data[self.data['time'] < new_kdata['time'].values[0]]
        self.data = concat([tmp_ori_data, new_kdata])
        self.data = self.data.reset_index(drop=True)
        return self


class BaseDataStruct:
    def __init__(self, code, kdata_dict):
        self.code = code
        self.kdata = dict()
        for frequency, kdata_df in kdata_dict.items():
            self.kdata[frequency] = KDataStruct(kdata_df)

    def get_kdata(self, frequency):
        return self.kdata[frequency]

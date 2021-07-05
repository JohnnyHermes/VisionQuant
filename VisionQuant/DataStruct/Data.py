from VisionQuant.utils import TimeTool
from numpy import datetime64
from datetime import datetime
from pandas import concat


class KDataStruct:
    def __init__(self, kdata_df):
        self.data = kdata_df

    def fliter(self, key, start, end, is_reset_index=False):
        if key == 'index':
            out_df = self.data[(self.data.index >= start) & (self.data.index <= end)]
        elif key in self.data.columns:
            if key == 'time':
                if type(start) == str:
                    start = TimeTool.str_to_npdt64(start)
                elif type(end) == datetime:
                    end = TimeTool.dt_to_npdt64(end)
            out_df = self.data[(self.data[key] >= start) & (self.data[key] <= end)]
        else:
            raise ValueError
        if is_reset_index:
            out_df = out_df.reset_index(drop=True)
        new_KDataStruct = KDataStruct(out_df)
        return new_KDataStruct

    def get_last_bar(self):
        return self.data.tail(1)

    def get_last_time(self):
        line = self.get_last_bar()
        t = TimeTool.time_standardization(line.time.values[0])
        return t

    def get_last_index(self):
        line = self.get_last_bar()
        i = line.index.values[0]
        return i

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

def kdata_filter(kdata_df, **kwargs):
    pass


class BaseDataStruct:
    def __init__(self, kdata_dict):
        self.kdata = kdata_dict

    def get_kdata(self, frequency, **kwargs):
        pass

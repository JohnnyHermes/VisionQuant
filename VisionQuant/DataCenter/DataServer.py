from VisionQuant.DataCenter import DataFetch
from VisionQuant.DataStruct.AShare import AShare
from VisionQuant.utils.Code import Code
from VisionQuant.utils import TimeTool
from VisionQuant.DataCenter import VQtdx_live


class DataServer:
    def __init__(self):
        self.data_dict = dict()

    def add_data(self, codes):
        if isinstance(codes, list):
            for code in codes:
                if isinstance(code, Code):
                    raise TypeError("Wrong code type")
                else:
                    data_dict = dict()
                    if isinstance(code.frequency, list):
                        for freq in code.frequency:
                            fetch_data = DataFetch.fetch_kdata(code=code.code,
                                                               frequency=freq,
                                                               method_func=code.fetch_data_method,
                                                               start_time=code.start_time,
                                                               end_time=code.end_time)
                            data_dict[freq] = fetch_data
                    else:
                        fetch_data = DataFetch.fetch_kdata(code=code.code,
                                                           frequency=code.frequency,
                                                           method_func=code.fetch_data_method,
                                                           start_time=code.start_time,
                                                           end_time=code.end_time)
                        data_dict[code.frequency] = fetch_data
                    self.data_dict[code.code] = AShare(code.code, data_dict)  # todo: 根据品种代码支持多品种
                    return self.data_dict[code.code]
        elif isinstance(codes, Code):
            data_dict = dict()
            fetch_data = DataFetch.fetch_kdata(code=codes.code,
                                               frequency=codes.frequency,
                                               method_func=codes.fetch_data_method,
                                               start_time=codes.start_time,
                                               end_time=codes.end_time)
            data_dict[codes.frequency] = fetch_data
            self.data_dict[codes.code] = AShare(codes.code, data_dict)  # todo: 根据品种代码支持多品种
            return self.data_dict[codes.code]
        else:
            raise ValueError

    def remove_data(self, codes):
        if isinstance(codes, list):
            for code in codes:
                if isinstance(code, Code):
                    raise TypeError("Wrong code type")
                if code.code in self.data_dict.keys():
                    del self.data_dict[code.code]
                else:
                    continue
        elif isinstance(codes, Code):
            if codes.code in self.data_dict.keys():
                del self.data_dict[codes.code]
            else:
                pass
        else:
            raise TypeError("Wrong codes type")

    def get_data(self, codes):
        if isinstance(codes, list):
            return_data = dict()
            for code in codes:
                if isinstance(code, Code):
                    raise TypeError("Wrong code type")
                if code.code in self.data_dict.keys():
                    return_data[code.code] = self._update_data(code)
                else:
                    return_data[code.code] = self.add_data(code)
            return return_data
        elif isinstance(codes, Code):
            if codes.code in self.data_dict.keys():
                return self._update_data(codes)
            else:
                return self.add_data(codes)
        else:
            raise TypeError("Wrong codes type")

    def _update_data(self, code):
        if TimeTool.is_trade_time(code.market):
            fetch_data = DataFetch.fetch_kdata(code=code.code,
                                                frequency=code.frequency,
                                                method_func=VQtdx_live,
                                                start_time=code.start_time,
                                                end_time=code.end_time)
            self.data_dict[code.code].get_kdata(code.frequency).update(fetch_data)
            return self.data_dict[code.code]
        else:
            return self.data_dict[code.code]

    # todo:这个函数暂时没用
    @staticmethod
    def _is_up_to_date(data):
        max_time_delta = 10
        is_live = TimeTool.is_trade_time(1)  # todo:修改市场信息
        if TimeTool.get_now_time() - data.get_last_time(is_live) > max_time_delta:
            return False
        else:
            return True

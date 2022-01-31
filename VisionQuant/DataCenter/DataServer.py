import datetime

import pandas as pd

from VisionQuant.DataCenter import DataFetch
from VisionQuant.DataStruct.AShare import AShare
from VisionQuant.utils.Code import Code
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import DATASERVER_MAX_COUNT


class DataServer:
    def __init__(self, force_live=False, max_count=DATASERVER_MAX_COUNT):
        self.force_live = force_live
        self.max_count = max_count
        self.basic_finance_data = None
        self.data_dict = dict()
        self.sk_client_mng = DataFetch.SocketClientsManager()
        self.last_update_time = TimeTool.get_now_time(return_type='datetime')

    def add_data(self, codes):
        if isinstance(codes, list):
            if len(codes) > self.max_count:
                codes = codes[:self.max_count]
                print("超过max_count,只取前{}个code".format(self.max_count))
                self.clean_data()
            elif len(codes) + len(self.data_dict) > self.max_count:
                self.clean_data()
            kdata_list = []
            for code in codes:
                tmp_code = code.copy()  # 拷贝一个副本，修改时间为最新，直接获取到最近时刻的数据，再fliter
                tmp_code.end_time = TimeTool.get_now_time()
                if isinstance(code, Code):
                    raise TypeError("Wrong code type")
                else:
                    data_dict = dict()
                    if isinstance(code.frequency, list):
                        for freq in code.frequency:
                            tmp_code.frequency = freq
                            socket_client = self.sk_client_mng.init_socket(*code.data_source_local.name)
                            try:
                                fetch_data = code.data_source_local.fetch_kdata(socket_client, tmp_code)
                            except Exception as e:
                                print(e)
                                data_dict[freq] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                        'high', 'low', 'volume', 'amount'])
                            else:
                                data_dict[freq] = fetch_data
                    else:
                        socket_client = self.sk_client_mng.init_socket(*code.data_source_local.name)
                        try:
                            fetch_data = code.data_source_local.fetch_kdata(socket_client, tmp_code)
                        except Exception as e:
                            print(e)
                            data_dict[code.frequency] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                              'high', 'low', 'volume', 'amount'])
                        else:
                            data_dict[code.frequency] = fetch_data
                    self.data_dict[code.code] = AShare(code, data_dict)  # todo: 根据品种代码支持多品种
                    if self.force_live or TimeTool.is_trade_time(code.market):
                        self.update_data(code)
                    kdata_list.append(self.data_dict[code.code].fliter(key='time',
                                                                       start=code.start_time, end=code.end_time))
            return kdata_list
        elif isinstance(codes, Code):
            if len(self.data_dict) + 1 > self.max_count:
                self.clean_data()
            data_dict = dict()
            tmp_code = codes.copy()  # 拷贝一个副本，修改时间为最新，直接获取到最近时刻的数据，再fliter
            tmp_code.end_time = TimeTool.get_now_time()
            if isinstance(codes.frequency, list):
                for freq in codes.frequency:
                    tmp_code.frequency = freq
                    socket_client = self.sk_client_mng.init_socket(*codes.data_source_local.name)
                    try:
                        fetch_data = codes.data_source_local.fetch_kdata(socket_client, tmp_code)
                    except Exception as e:
                        print(e)
                        data_dict[freq] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                'high', 'low', 'volume', 'amount'])
                    else:
                        data_dict[freq] = fetch_data
            else:
                socket_client = self.sk_client_mng.init_socket(*codes.data_source_local.name)
                try:
                    fetch_data = codes.data_source_local.fetch_kdata(socket_client, tmp_code)
                except Exception as e:
                    print(e)
                    data_dict[codes.frequency] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                       'high', 'low', 'volume', 'amount'])
                else:
                    data_dict[codes.frequency] = fetch_data
            self.data_dict[codes.code] = AShare(codes, data_dict)  # todo: 根据品种代码支持多品种
            if self.force_live or TimeTool.is_trade_time(codes.market):
                self.update_data(codes)
            return self.data_dict[codes.code].fliter(key='time', start=codes.start_time, end=codes.end_time)
        else:
            raise ValueError

    def remove_data(self, codes=None):
        if codes is None:
            self.clean_data()
        else:
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

    def clean_data(self):
        del self.data_dict
        self.data_dict = dict()

    def get_data(self, codes):
        if isinstance(codes, list):
            return_data = dict()
            for code in codes:
                print("send kdata: {} start_time:{} end_time:{}".format(code.code, code.start_time, code.end_time))
                if isinstance(code, Code):
                    raise TypeError("Wrong code type")
                if code.code in self.data_dict.keys():
                    if self.force_live or TimeTool.is_trade_time(code.market):
                        return_data[code.code] = self.update_data(code).fliter(key='time', start=code.start_time,
                                                                               end=code.end_time)
                    else:
                        if not isinstance(code.frequency, list):
                            freq = code.frequency
                        else:
                            freq = code.frequency[0]
                        if self.data_dict[code.code].get_kdata(freq).get_start_time() > \
                                TimeTool.time_standardization(code.start_time):
                            self.add_data(code)
                        tmp_datastruct = self.data_dict[code.code].fliter(key='time',
                                                                          start=code.start_time, end=code.end_time)
                        return_data[code.code] = tmp_datastruct
                else:
                    return_data[code.code] = self.add_data(code)
            return return_data
        elif isinstance(codes, Code):
            print("send kdata: {} start_time:{} end_time:{}".format(codes.code, codes.start_time, codes.end_time))
            if codes.code in self.data_dict.keys():
                if self.force_live or TimeTool.is_trade_time(codes.market):
                    tmp_datastruct = self.update_data(codes).fliter(key='time',
                                                                    start=codes.start_time, end=codes.end_time)
                    return tmp_datastruct
                else:
                    if not isinstance(codes.frequency, list):
                        freq = codes.frequency
                    else:
                        freq = codes.frequency[0]
                    if self.data_dict[codes.code].get_kdata(freq).get_start_time() >\
                            TimeTool.time_standardization(codes.start_time):
                        self.add_data(codes)
                    tmp_datastruct = self.data_dict[codes.code].fliter(key='time',
                                                                       start=codes.start_time, end=codes.end_time)
                    return tmp_datastruct
            else:
                return self.add_data(codes)
        else:
            raise TypeError("Wrong codes type")

    def update_data(self, code):
        now_time = TimeTool.get_now_time(return_type='datetime')
        if not isinstance(code.frequency, list) and len(self.data_dict[code.code].get_kdata(code.frequency).data) > 0 \
                and code.end_time <= self.data_dict[code.code].get_kdata(code.frequency).get_last_time():
            return self.data_dict[code.code]
        if now_time - self.last_update_time > datetime.timedelta(seconds=120):
            if self.sk_client_mng.find(code.data_source_live.name[0]):
                self.sk_client_mng.close_socket(code.data_source_live.name[0])
            socket_client = self.sk_client_mng.init_socket(*code.data_source_live.name)
        else:
            socket_client = self.sk_client_mng.init_socket(*code.data_source_live.name)
        if isinstance(code.frequency, list):
            tmp_code = code.copy()
            tmp_code.start_time = code.end_time
            tmp_code.end_time = TimeTool.get_now_time()
            for freq in code.frequency:
                tmp_code.frequency = freq
                fetch_data = code.data_source_live.fetch_kdata(socket_client, tmp_code)
                self.data_dict[code.code].get_kdata(freq).update(fetch_data)
        else:
            tmp_code = code.copy()
            tmp_code.start_time = code.end_time
            tmp_code.end_time = TimeTool.get_now_time()
            fetch_data = code.data_source_live.fetch_kdata(socket_client, tmp_code)
            self.data_dict[code.code].get_kdata(code.frequency).update(fetch_data)
        self.last_update_time = TimeTool.get_now_time(return_type='datetime')
        return self.data_dict[code.code]

    def get_basic_finance_data(self, code):
        if self.basic_finance_data is None:
            res = dict()
            from VisionQuant.utils.Params import Stock
            if code.market in [Stock.Ashare.MarketSH.STOCK, Stock.Ashare.MarketSZ.STOCK]:
                from mootdx.quotes import Quotes
                client = Quotes.factory(market='std')
                data1 = client.F10(symbol=code.code, name='股本结构')
                start_index = data1.find("实际流通A股")
                data2 = data1[start_index:data1.find('\r\n', start_index)]
                data2 = data2.split('│')
                data2 = list(map(lambda s: s.strip(), data2))
                final_data = round(float(data2[1]) * 10000)
                res['流通股本'] = final_data
                return res
            else:
                return res
        else:
            pass
            # todo:本地读取

    # todo:这个函数暂时没用
    @staticmethod
    def _is_up_to_date(data):
        max_time_delta = 10
        is_live = TimeTool.is_trade_time(1)  # todo:修改市场信息
        if TimeTool.get_now_time() - data.get_last_time(is_live) > max_time_delta:
            return False
        else:
            return True

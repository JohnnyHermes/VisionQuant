import datetime

import psutil
import pandas as pd

from VisionQuant.DataCenter import DataFetch
from VisionQuant.DataStruct.AShare import AShare, Future
from VisionQuant.utils.Code import Code
from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import DATASERVER_MIN_FREE_MEM, MarketType

from threading import Semaphore

# 加一个信号锁，HqServer多线程时不会导致与Tdx服务器socket通信发生错误
semaphore = Semaphore(1)


class KDataServer:
    def __init__(self, force_live=False, min_free_mem=DATASERVER_MIN_FREE_MEM):
        self.force_live = force_live
        self.data_dict = dict()
        self.min_free_mem = min_free_mem
        self.source_mng = DataFetch.SocketClientsManager()
        self._last_update_time = TimeTool.get_now_time(return_type='datetime')

    def get_data(self, code: Code):
        if semaphore.acquire():
            code_key = self.get_code_key(code)
            if code_key not in self.data_dict.keys():
                self.check_free_mem()
                self._add_local_data(code)
            if self.force_live:
                self._update_data(code)
                data = self.data_dict[code_key].filter(key='time', start=code.start_time, freqs=code.frequency)
                print("send kdata: {} start_time:{} end_time:{}".format(code.code, code.start_time, code.end_time))
                semaphore.release()
                return data
            else:
                not_available_freqs = []
                available_freqs = self.data_dict[code_key].get_freqs()
                if isinstance(code.frequency, list):
                    for freq in code.frequency:
                        if freq not in available_freqs:
                            not_available_freqs.append(freq)
                else:
                    if code.frequency not in available_freqs:
                        not_available_freqs.append(code.frequency)
                if not_available_freqs:
                    tmp_code = code.copy()
                    tmp_code.frequency = not_available_freqs
                    self.add_new_freq_kdata(tmp_code)

                end_date = TimeTool.time_to_str(code.end_time, '%Y-%m-%d')
                nearest_trade_date_end = TimeTool.get_nearest_trade_date(code.end_time, code.market, flag='end')
                nearest_trade_date_start = TimeTool.get_nearest_trade_date(code.start_time, code.market, flag='start')
                data_last_date = self.data_dict[code_key].get_last_time(code.frequency)
                data_start_date = self.data_dict[code_key].get_start_time(code.frequency)
                # print(end_date)
                # print(nearest_trade_date_start,nearest_trade_date_end)
                # print(data_start_date,data_last_date)
                # print("本地数据范围：{} {}".format(data_start_date,data_last_date))
                # print(data_start_date, data_last_date, nearest_trade_date_start, nearest_trade_date_end)
                if isinstance(code.frequency, list):
                    tmp_code = code.copy()

                    repair_freqs = []
                    for freq, start_date in data_start_date.items():
                        _start_date = TimeTool.time_to_str(start_date, '%Y-%m-%d')
                        if _start_date is None or _start_date > nearest_trade_date_start:
                            repair_freqs.append(freq)
                    tmp_code.frequency = repair_freqs
                    self._repair_data(tmp_code)

                    update_freqs = []
                    for freq, last_date in data_last_date.items():
                        _last_date = TimeTool.time_to_str(last_date, '%Y-%m-%d')
                        if _last_date is None:
                            update_freqs.append(freq)
                        elif _last_date < end_date:
                            if _last_date < nearest_trade_date_end:
                                update_freqs.append(freq)
                        elif _last_date == end_date:
                            if TimeTool.is_trade_time(code.market):
                                update_freqs.append(freq)
                    tmp_code.frequency = update_freqs
                    self._update_data(tmp_code)

                    data_last_date = TimeTool.time_to_str(self.data_dict[code_key].get_last_time(
                        code.frequency[0]), '%Y-%m-%d')
                    if data_last_date == end_date:
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time, freqs=code.frequency)
                    else:
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time, end=code.end_time,
                                                               freqs=code.frequency)
                    print("send kdata: {} start_time:{} end_time:{}".format(code.code, code.start_time, code.end_time))
                    semaphore.release()
                    return data
                else:
                    data_last_date = TimeTool.time_to_str(data_last_date, '%Y-%m-%d')
                    data_start_date = TimeTool.time_to_str(data_start_date, '%Y-%m-%d')
                    if data_start_date is None or data_start_date > nearest_trade_date_start:
                        self._repair_data(code)

                    if data_last_date is None:
                        self._update_data(code)
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time, end=code.end_time,
                                                               freqs=code.frequency)
                    elif data_last_date < end_date:
                        if data_last_date < nearest_trade_date_end:
                            self._update_data(code)
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time, end=code.end_time,
                                                               freqs=code.frequency)
                    elif data_last_date == end_date:
                        if TimeTool.is_trade_time(code.market):
                            self._update_data(code)
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time,
                                                               freqs=code.frequency)
                    else:
                        data = self.data_dict[code_key].filter(key='time', start=code.start_time, end=code.end_time,
                                                               freqs=code.frequency)
                    print("send kdata: {} start_time:{} end_time:{}".format(code.code, code.start_time, code.end_time))
                    semaphore.release()
                    return data

    def add_new_freq_kdata(self, code: Code):
        tmp_code = code.copy()
        tmp_code.end_time = TimeTool.get_now_time()
        data_source = self.select_local_source(tmp_code)
        code_key = self.get_code_key(tmp_code)
        data_dict = dict()
        for freq in code.frequency:
            tmp_code.frequency = freq
            socket_client = self.source_mng.init_socket(data_source)
            try:
                fetch_data = data_source.fetch_kdata(socket_client, tmp_code)
            except Exception as e:
                print(e)
                data_dict[tmp_code.frequency] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                      'high', 'low', 'volume'])
            else:
                data_dict[tmp_code.frequency] = fetch_data
        self.data_dict[code_key].add_kdata(data_dict)

    def _add_local_data(self, code: Code):
        def get_single_freq_data(_code: Code):
            socket_client = self.source_mng.init_socket(data_source)
            try:
                fetch_data = data_source.fetch_kdata(socket_client, _code)
            except Exception as e:
                print(e)
                data_dict[_code.frequency] = pd.DataFrame(columns=['time', 'open', 'close',
                                                                   'high', 'low', 'volume'])
            else:
                data_dict[_code.frequency] = fetch_data

        tmp_code = code.copy()
        data_source = self.select_local_source(code)
        tmp_code.end_time = TimeTool.get_now_time()
        data_dict = dict()
        if isinstance(code.frequency, list):
            for freq in code.frequency:
                tmp_code.frequency = freq
                get_single_freq_data(tmp_code)
        else:
            get_single_freq_data(tmp_code)
        code_key = self.get_code_key(code)
        if MarketType.is_ashare(code.market):
            self.data_dict[code_key] = AShare(code, data_dict)
        elif MarketType.is_future(code.market):
            self.data_dict[code_key] = Future(code, data_dict)
        else:
            raise ValueError  # todo: 根据品种代码支持多品种

    def _update_data(self, code: Code):

        def update_single_freq_data(_code: Code):
            if now_time - self._last_update_time > datetime.timedelta(seconds=120):
                if self.source_mng.find(data_source):
                    self.source_mng.close_socket(data_source)
            try:
                socket_client = self.source_mng.init_socket(data_source)
                _fetch_data = data_source.fetch_kdata(socket_client, _code)
            except Exception as e:
                print(e)
                if MarketType.is_ashare(_code.market):
                    columns = ['time', 'open', 'close', 'high', 'low', 'volume']
                elif MarketType.is_future(_code.market):
                    columns = ['time', 'open', 'close', 'high', 'low', 'volume']
                else:
                    columns = ['time', 'open', 'close', 'high', 'low', 'volume']
                _fetch_data = pd.DataFrame(columns=columns)
            return _fetch_data

        now_time = TimeTool.get_now_time(return_type='datetime')
        data_source = self.select_live_source(code)
        code_key = self.get_code_key(code)

        tmp_code = code.copy()
        tmp_code.start_time = TimeTool.get_start_time(tmp_code.end_time, days=7)
        tmp_code.end_time = TimeTool.time_plus(tmp_code.end_time, days=7)

        if isinstance(code.frequency, list):
            for freq in code.frequency:
                tmp_code.frequency = freq
                fetch_data = update_single_freq_data(tmp_code)
                self.data_dict[code_key].get_kdata(freq).update(fetch_data)
        else:
            fetch_data = update_single_freq_data(tmp_code)
            self.data_dict[code_key].get_kdata(code.frequency).update(fetch_data)

        self._last_update_time = now_time

    def _repair_data(self, code):
        data_source = self.select_local_source(code)
        tmp_code = code.copy()
        tmp_code.start_time = TimeTool.get_start_time(tmp_code.start_time, days=7)
        # tmp_code.end_time = TimeTool.time_plus(tmp_code.start_time, days=7)
        code_key = self.get_code_key(code)
        socket_client = self.source_mng.init_socket(data_source)
        if isinstance(code.frequency, list):
            for freq in code.frequency:
                tmp_code.frequency = freq
                fetch_data = data_source.fetch_kdata(socket_client, tmp_code)
                self.data_dict[code_key].get_kdata(freq).repair(fetch_data)
        else:
            fetch_data = data_source.fetch_kdata(socket_client, tmp_code)
            self.data_dict[code_key].get_kdata(code.frequency).repair(fetch_data)

    def check_free_mem(self):
        mem = psutil.virtual_memory()
        if mem.free / (1024 * 1024) < self.min_free_mem:
            self.clean_data()

    def clean_data(self):
        del self.data_dict
        self.data_dict = dict()

    @staticmethod
    def get_code_key(code: Code):
        return code.code + code.market.name

    @staticmethod
    def select_local_source(code: Code):
        if MarketType.is_ashare(code.market):
            return DataFetch.DEFAULT_ASHARE_LOCAL_DATASOURCE
        elif MarketType.is_future(code.market):
            return DataFetch.DEFAULT_FUTURE_LOCAL_DATASOURCE
        else:
            raise ValueError

    @staticmethod
    def select_live_source(code: Code):
        if MarketType.is_ashare(code.market):
            return DataFetch.DEFAULT_ASHARE_LIVE_DATASOURCE
        elif MarketType.is_future(code.market):
            return DataFetch.DEFAULT_FUTURE_LIVE_DATASOURCE
        else:
            raise ValueError


class FinancialDataServer:
    def __init__(self):
        self.basic_finance_data = None
        self.source_mng = DataFetch.SocketClientsManager()

    def get_basic_financial_data(self, code):
        if code.market not in [MarketType.Ashare.SH.STOCK, MarketType.Ashare.SZ.STOCK]:
            return None
        if self.basic_finance_data is None:
            data_source = DataFetch.DEFAULT_BASIC_FINANCE_DATA_DATASOURCE
            sk = self.source_mng.init_socket(data_source)
            self.basic_finance_data = data_source.fetch_basic_finance_data(sk, MarketType.Ashare)
            if len(self.basic_finance_data) == 0:
                return None
                # res = dict()
                # if code.market in [Market.Ashare.MarketSH.STOCK, Market.Ashare.MarketSZ.STOCK]:
                #     from mootdx.quotes import Quotes
                #     client = Quotes.factory(market='std')
                #     data1 = client.F10(symbol=code.code, name='股本结构')
                #     start_index = data1.find("实际流通A股")
                #     data2 = data1[start_index:data1.find('\r\n', start_index)]
                #     data2 = data2.split('│')
                #     data2 = list(map(lambda s: s.strip(), data2))
                #     final_data = round(float(data2[1]) * 10000)
                #     res['流通股本'] = final_data
                #     return res
                # else:
                #     return res
            else:
                code_line = self.basic_finance_data[self.basic_finance_data['代码'] == code.code]
                if len(code_line) == 0:
                    return None
                res = dict()
                for key in ('流通股本', '市盈率-动态', "市净率"):
                    res[key] = code_line[key].values[0]
                return res
        else:
            code_line = self.basic_finance_data[self.basic_finance_data['代码'] == code.code]
            if len(code_line) == 0:
                return None
            res = dict()
            for key in ('流通股本', '市盈率-动态', "市净率"):
                res[key] = code_line[key].values[0]
            return res


class DataServer:
    def __init__(self, force_live=False, min_free_mem=DATASERVER_MIN_FREE_MEM):
        self.kdata_server = KDataServer(force_live=force_live, min_free_mem=min_free_mem)
        self.financial_data_server = FinancialDataServer()

    def get_kdata(self, code: Code):
        return self.kdata_server.get_data(code)

    def get_basic_financial_data(self, code: Code):
        return self.financial_data_server.get_basic_financial_data(code)

    def configure(self, settings_dict: dict):
        if 'force_live' in settings_dict.keys():
            self.kdata_server.force_live = settings_dict['force_live']
            print("修改参数force_live为{}".format(self.kdata_server.force_live))
        if 'max_count' in settings_dict.keys():
            self.kdata_server.max_count = settings_dict['max_count']
            print("修改参数force_live为{}".format(self.kdata_server.max_count))
        if 'clean_data' in settings_dict.keys():
            self.kdata_server.clean_data()
            print("清除缓存数据！")

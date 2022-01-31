import json
import time

import numpy as np
import requests
import pandas as pd
from path import Path
from socket import timeout
from VisionQuant.DataCenter.VQTdx.TdxHqAPI import ResponseRecvFailed, SendRequestPkgFailed, ResponseHeaderRecvFailed
from VisionQuant.utils import TimeTool, JsonTool
from VisionQuant.DataCenter.VQTdx.TdxSocketClient import TdxStdHqSocketClient
from VisionQuant.DataCenter.VQTdx.TdxReader import TdxStdReader
from VisionQuant.utils.Params import Stock, LOCAL_DIR, HDF5_COMPLIB, HDF5_COMP_LEVEL, EXCEPT_CODELIST, REMOTE_ADDR
from retrying import retry


class SocketClientsManager(object):
    def __init__(self):
        self._sockets = dict()

    def init_socket(self, data_source_name, data_source):
        if data_source_name in self._sockets:
            # print("已存在该socket_clinet")
            return self.get_socket(data_source_name)
        else:
            socket_client = data_source()
            self._sockets[data_source_name] = socket_client.init_socket()  # 加入字典并实例化
            return self._sockets[data_source_name]

    def get_socket(self, socket_name):
        return self._sockets[socket_name]

    def close_socket(self, socket_name):
        self._sockets[socket_name].close()
        del self._sockets[socket_name]

    def find(self, socket_name):
        if socket_name in self._sockets:
            return True
        else:
            return False


class DataSourceTdxLive(object):
    name = ('tdx_live', TdxStdHqSocketClient)

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_kdata(socket_client, code):
        try:
            fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                        code=code.code,
                                                        market=code.market,
                                                        freq=code.frequency,
                                                        count=800)
        except (ResponseRecvFailed, SendRequestPkgFailed, timeout, ResponseHeaderRecvFailed):
            print("连接至服务器失败，重新尝试链接...")
            flg = socket_client.reconnect()
            if flg:
                print("重新连接成功")
            raise ResponseRecvFailed
        else:
            if len(fetched_kdata) == 0:
                return fetched_kdata
            # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
            fetched_kdata.drop(fetched_kdata[fetched_kdata['volume'] == 0].index, inplace=True)
            fetched_kdata.reset_index(drop=True, inplace=True)
        return fetched_kdata

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_codelist(socket_client, market=Stock.Ashare):
        def flitercode(code: str):
            if (code.startswith('51') or code.startswith('58')) and code[-1] != '0':
                return 0
            elif code in EXCEPT_CODELIST or '519000' <= code < '600000':
                return 0
            else:
                return 1

        try:
            data = socket_client.api.get_stocks_list(socket_client.socket, market)
        except (ResponseRecvFailed, SendRequestPkgFailed, timeout):
            print("连接至服务器失败，重新尝试链接...")
            socket_client.init_socket()
            raise ResponseRecvFailed
        else:
            data['flag'] = data['code'].apply(flitercode)
            data.drop(data[data['flag'] == 0].index, inplace=True)
            data.drop(columns=['flag'], inplace=True)
        return data

    def fetch_latest_quotes(self, sock_client, code: object):
        pass


class DataSourceTdxLocal(object):
    name = ('tdx_local', TdxStdReader)

    @staticmethod
    def fetch_kdata(socket_client, code):
        fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                    code=code.code,
                                                    market=code.market,
                                                    freq=code.frequency)
        if len(fetched_kdata) == 0:
            return fetched_kdata
        out_df = fetched_kdata[(fetched_kdata['time'] >= code.start_time) &
                               (fetched_kdata['time'] <= code.end_time)]
        out_df.reset_index(drop=True, inplace=True)
        return out_df


class LocalReaderAPI(object):
    @staticmethod
    def get_kdata(reader, code, market, freq):
        try:
            datapath = reader.find_path_kdata(code, market)
            store = pd.HDFStore(datapath, mode='r', complib=HDF5_COMPLIB, complevel=HDF5_COMP_LEVEL)
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['time', 'open', 'close', 'high', 'low', 'volume', 'amount'])
        else:
            try:
                df = store.get('_' + freq)
            except KeyError:
                print("未储存此frequency的数据:{}".format(freq))
                store.close()
                return pd.DataFrame(columns=['time', 'open', 'close', 'high', 'low', 'volume', 'amount'])
            else:
                store.close()
                return df

    @staticmethod
    def get_codelist(reader, market=Stock.Ashare):
        try:
            datapath = reader.find_path_codelist(market)
            code_list = pd.read_csv(datapath, encoding='utf-8', dtype={'code': str, 'name': str, 'market': int})
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['code', 'name', 'market'])
        else:
            return code_list


class LocalReader(object):
    localdir = None

    def __init__(self):
        self.socket = self
        self.api = LocalReaderAPI()

    def init_socket(self):
        if Path(LOCAL_DIR).isdir():
            self.localdir = LOCAL_DIR
        else:
            raise OSError('HDF5 Reader:{} 目录不存在'.format(LOCAL_DIR))
        return self

    def find_path_kdata(self, code, market):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """
        if self.localdir is None:
            raise RuntimeError("没有init socket")
        market, market_type = self.market_transform(market)
        if market_type is None:
            fname = code + '.h5'
        else:
            fname = market_type + code + '.h5'

        path = Path('/'.join([self.localdir, 'KData', market, fname]))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    def find_path_codelist(self, market):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """

        def market_transform(_market):
            if _market is Stock.Ashare:
                return 'ashare'
            else:  # todo:增加不同市场类型
                return 'future'

        if self.localdir is None:
            raise RuntimeError("没有init socket")

        market_str = market_transform(market)
        path = Path('/'.join([self.localdir, 'code_list_' + market_str + '.csv']))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    @staticmethod
    def market_transform(market):
        if market in [Stock.Ashare.MarketSH, Stock.Ashare.MarketSH.STOCK, Stock.Ashare.MarketSH.ETF,
                      Stock.Ashare.MarketSH.INDEX, Stock.Ashare.MarketSH.KCB]:
            return 'Ashare', 'sh'
        elif market in [Stock.Ashare.MarketSZ, Stock.Ashare.MarketSZ.STOCK, Stock.Ashare.MarketSZ.ETF,
                        Stock.Ashare.MarketSZ.INDEX, Stock.Ashare.MarketSZ.CYB]:
            return 'Ashare', 'sz'
        else:
            raise ValueError("错误的市场类型")

    def close(self):
        self.localdir = None


class DataSourceLocal(object):
    name = ('local', LocalReader)

    @staticmethod
    def fetch_kdata(socket_client, code):
        fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                    code=code.code,
                                                    market=code.market,
                                                    freq=code.frequency)
        if len(fetched_kdata) == 0:
            return fetched_kdata
        out_df = fetched_kdata[(fetched_kdata['time'] >= code.start_time) &
                               (fetched_kdata['time'] <= code.end_time)]
        out_df.reset_index(drop=True, inplace=True)
        return out_df

    @staticmethod
    def fetch_codelist(socket_client, market):
        codelist = socket_client.api.get_codelist(socket_client.socket,
                                                  market=market)

        return codelist[['code', 'name', 'market']]


class RequestGenerater(object):
    remote_addr = None

    def __init__(self):
        self.socket = self
        self.api = RemoteServerAPI()

    def init_socket(self):
        if requests.get(REMOTE_ADDR).status_code == 200:
            self.remote_addr = REMOTE_ADDR
        else:
            raise OSError('与远程服务器{} API测试连接错误！'.format(REMOTE_ADDR))
        return self

    def generate_kdata_url(self, code: str, freq: str, market, st, et):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")

        get_url = self.remote_addr + '/kdata/?'
        code_str = 'code=' + code
        freq_str = 'freq=' + freq
        market_str = 'market=' + str(market)
        st_str = 'st=' + TimeTool.time_to_str(st, '%Y%m%d%H%M%S')
        et_str = 'et=' + TimeTool.time_to_str(et, '%Y%m%d%H%M%S')
        get_url = get_url + code_str + '&' + freq_str + '&' + market_str + '&' + st_str + '&' + et_str
        return get_url

    def generate_codelist_url(self, market):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """

        def market_transform(_market):
            if _market is Stock.Ashare:
                return 'ashare'
            else:  # todo:增加不同市场类型
                return 'future'

        if self.remote_addr is None:
            raise RuntimeError("没有init socket")

        market_str = market_transform(market)
        get_url = self.remote_addr + '/codelist/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

    @staticmethod
    def market_transform(market):
        if market in [Stock.Ashare.MarketSH, Stock.Ashare.MarketSH.STOCK, Stock.Ashare.MarketSH.ETF,
                      Stock.Ashare.MarketSH.INDEX, Stock.Ashare.MarketSH.KCB]:
            return 'Ashare', 'sh'
        elif market in [Stock.Ashare.MarketSZ, Stock.Ashare.MarketSZ.STOCK, Stock.Ashare.MarketSZ.ETF,
                        Stock.Ashare.MarketSZ.INDEX, Stock.Ashare.MarketSZ.CYB]:
            return 'Ashare', 'sz'
        else:
            raise ValueError("错误的市场类型")

    def close(self):
        self.remote_addr = None


class RemoteServerAPI(object):

    @staticmethod
    def get_kdata(req_generater, code, freq, market, st, et):
        get_url = req_generater.generate_kdata_url(code=code,
                                                   freq=freq,
                                                   market=market,
                                                   st=st,
                                                   et=et)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            kdata = data['data']
            return JsonTool.getdata_from_json(kdata)
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_codelist(req_generater, market=Stock.Ashare):
        get_url = req_generater.generate_codelist_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            return JsonTool.getdata_from_json(data['data'], dtype={'code': str, 'name': str, 'market': int})
        else:
            raise ValueError("VQapi返回msg 为 false")


class DataSourceVQAPI(object):
    name = ('VQAPI', RequestGenerater)

    @staticmethod
    def fetch_kdata(socket_client, code):
        fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                    code=code.code,
                                                    freq=code.frequency,
                                                    market=code.market,
                                                    st=code.start_time,
                                                    et=code.end_time
                                                    )
        if len(fetched_kdata) == 0:
            return fetched_kdata
        # 时间反序列化
        fetched_kdata['time'] = fetched_kdata['time'].apply(TimeTool.time_standardization)
        fetched_kdata['volume'] = fetched_kdata['volume'].astype(np.float64)
        fetched_kdata.reset_index(drop=True, inplace=True)
        return fetched_kdata

    @staticmethod
    def fetch_codelist(socket_client, market):
        codelist = socket_client.api.get_codelist(socket_client.socket,
                                                  market=market)

        return codelist[['code', 'name', 'market']]


class AnalyzeDataReader:
    def __init__(self):
        self.localdir = Path('/'.join([LOCAL_DIR, 'AnalyzeData']))

    def get_relavity_score_data(self, key='Ashare'):
        fname = 'relavity_analyze_result.h5'
        try:
            datapath = self.find_path_anaresult(fname)
            store = pd.HDFStore(datapath, mode='r', complib=HDF5_COMPLIB, complevel=HDF5_COMP_LEVEL)
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
        else:
            try:
                df = store.get(key=key)
            except KeyError:
                print("未储存此市场的数据:{}".format(key))
                store.close()
                return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
            else:
                store.close()
                return df

    def find_path_anaresult(self, fname):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """

        path = Path('/'.join([self.localdir, fname]))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path


def mergeKdata(kdata, period, new_period):
    interval = int(int(new_period) / int(period))
    count = 0
    data_list = []
    while count < len(kdata):
        tmp_data = kdata[count:count + interval]
        tmp_high = tmp_data['high'].max()
        tmp_low = tmp_data['low'].min()
        tmp_open = tmp_data['open'].iloc[0]
        tmp_close = tmp_data['close'].iloc[len(tmp_data['close']) - 1]
        tmp_amount = tmp_data['amount'].sum()
        tmp_volume = tmp_data['volume'].sum()
        tmp_time = tmp_data['time'].iloc[len(tmp_data['time']) - 1]
        data_list.append((tmp_open, tmp_high, tmp_low, tmp_close, tmp_volume, tmp_amount, tmp_time))
        count = count + interval
    new_out_df = pd.DataFrame(data_list, columns=['open', 'high', 'low', 'close', 'volume', 'amount', 'time'])
    return new_out_df


"""
数据获取方法
"""


class DataSource(object):
    class Local:
        VQtdx = DataSourceTdxLocal
        VQapi = DataSourceVQAPI
        Default = DataSourceLocal

    class Live:
        VQtdx = DataSourceTdxLive
        VQapi = DataSourceVQAPI


if __name__ == '__main__':
    sk_client_mng = SocketClientsManager()
    from VisionQuant.utils.Code import Code

    test_code = Code('002382', '1', start_time='2020-3-2', data_source={'local': DataSource.Local.Default})
    # test_socket_client_local = sk_client_mng.init_socket(*test_code.data_source_local.name)
    # test_fetch_data = test_code.data_source_local.fetch_kdata(test_socket_client_local, test_code)
    # print(test_fetch_data[-48:])
    test_socket_client_live = sk_client_mng.init_socket(*test_code.data_source_live.name)
    test_fetch_data = test_code.data_source_live.fetch_kdata(test_socket_client_live, test_code)
    print(test_fetch_data[-50:])

    # test_socket_client_live = sk_client_mng.init_socket(*test_code.data_source_live.name)
    # test_stock_list = test_code.data_source_live.fetch_codelist(test_socket_client_live)
    # from VisionQuant.DataCenter.DataStore import store_code_list_stock
    #
    # store_code_list_stock(test_stock_list, Stock.Ashare)

    from VisionQuant.DataCenter.DataStore import store_kdata_to_hdf5
    from VisionQuant.DataStruct.AShare import AShare
    from VisionQuant.utils.Params import Freq

    # t1 = time.perf_counter()
    # test_datastruct = AShare(code=test_code, kdata_dict={Freq.MIN5: test_fetch_data})
    # store_kdata_to_hdf5(test_datastruct)
    # t2 = time.perf_counter()
    # print(t2 - t1)

    # new_test_code = test_code.copy()
    # new_test_code.data_source_local = DataSource.Local.Default
    # test_socket_client_local = sk_client_mng.init_socket(*new_test_code.data_source_local.name)

    # t1 = time.perf_counter()
    # test_fetch_data = test_code.data_source_local.fetch_kdata(test_socket_client_local, test_code)
    # t2 = time.perf_counter()
    # print(t2 - t1)
    # print(test_fetch_data)
    # test_stock_list_local = new_test_code.data_source_local.fetch_codelist(test_socket_client_local, Stock.Ashare)
    # print(test_stock_list_local)

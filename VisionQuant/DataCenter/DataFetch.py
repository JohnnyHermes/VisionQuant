import json
import time
import numpy as np
import requests
import pandas as pd
from path import Path
from socket import timeout
from retrying import retry
from tqdm import tqdm

from VisionQuant.DataCenter.VQTdx.TdxHqAPI import ResponseRecvFailed, SendRequestPkgFailed, ResponseHeaderRecvFailed
from VisionQuant.utils import TimeTool, JsonTool
from VisionQuant.DataCenter.VQTdx.TdxSocketClient import TdxStdHqSocketClient, TdxExtHqSocketClient
from VisionQuant.DataCenter.VQTdx.TdxReader import TdxStdReader
from VisionQuant.utils.Params import MarketType, LOCAL_DIR, HDF5_COMPLIB, HDF5_COMP_LEVEL, EXCEPT_CODELIST, REMOTE_ADDR, \
    ASHARE_LOCAL_DATASOURCE, ASHARE_LIVE_DATASOURCE, CODELIST_DATASOURCE, \
    BLOCKS_DATA_DATASOURCE, BASIC_FINANCE_DATA_DATASOURCE
from VisionQuant.DataCenter.DataStore import anadata_store_market_transform, kdata_store_market_transform
from VisionQuant.utils.VQlog import logger


class FetchDataFailed(Exception):
    pass


class DataSourceBase(object):
    name = None
    sk_client = None


class SocketClientsManager(object):
    def __init__(self):
        self._sockets = dict()

    def init_socket(self, data_source: DataSourceBase):
        if data_source.name in self._sockets:
            return self.get_socket(data_source)
        else:
            socket_client = data_source.sk_client()
            self._sockets[data_source.name] = socket_client.init_socket()  # 加入字典并实例化
            return self._sockets[data_source.name]

    def get_socket(self, data_source: DataSourceBase):
        return self._sockets[data_source.name]

    def close_socket(self, data_source: DataSourceBase):
        self._sockets[data_source.name].close()
        del self._sockets[data_source.name]

    def find(self, data_source: DataSourceBase):
        if data_source.name in self._sockets:
            return True
        else:
            return False


class DataSourceTdxLive(DataSourceBase):
    name = 'tdx_live'
    sk_client = TdxStdHqSocketClient

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_kdata(socket_client, code):
        try:
            fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                        code=code.code,
                                                        market=code.market,
                                                        freq=code.frequency,  # 这里不同访问freq的value属性，api自动转换
                                                        count=800)
        except (ResponseRecvFailed, SendRequestPkgFailed, timeout, ResponseHeaderRecvFailed):
            logger.warning("连接至通达信服务器失败，重新尝试链接...")
            flg = socket_client.reconnect()
            if flg:
                logger.info("重新连接至通达信服务器成功")
            raise ResponseRecvFailed
        else:
            if len(fetched_kdata) == 0:
                return fetched_kdata
            # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
            # fetched_kdata.drop(fetched_kdata[fetched_kdata['volume'] == 0].index, inplace=True)
            # fetched_kdata.reset_index(drop=True, inplace=True)
        return fetched_kdata

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_codelist(socket_client, market=MarketType.Ashare):
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
            logger.warning("连接至通达信服务器失败，重新尝试链接...")
            socket_client.init_socket()
            flg = socket_client.reconnect()
            if flg:
                logger.info("重新连接至通达信服务器成功")
            raise ResponseRecvFailed
        else:
            data['flag'] = data['code'].apply(flitercode)
            data.drop(data[data['flag'] == 0].index, inplace=True)
            data.drop(columns=['flag'], inplace=True)
        return data

    def fetch_latest_quotes(self, sock_client, code: object):
        pass


class DataSourceExtTdxLive(DataSourceBase):
    name = 'tdx_live'
    sk_client = TdxExtHqSocketClient

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_kdata(socket_client, code):
        try:
            fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                        code=code.code,
                                                        market=code.market.value,
                                                        freq=code.frequency,  # 这里不同访问freq的value属性，api自动转换
                                                        count=700)
        except (ResponseRecvFailed, SendRequestPkgFailed, timeout, ResponseHeaderRecvFailed):
            logger.warning("连接至通达信服务器失败，重新尝试链接...")
            flg = socket_client.reconnect()
            if flg:
                logger.info("重新连接至通达信服务器成功")
            raise ResponseRecvFailed
        else:
            if len(fetched_kdata) == 0:
                return fetched_kdata
            fix = 2
            if code.market == MarketType.Future.ZJ and code.code[0] == 'T':
                fix = 3
            fix_columns = ['open', 'close', 'high', 'low']
            fetched_kdata[fix_columns] = fetched_kdata[fix_columns].apply(np.round, args=(fix,))
            fetched_kdata['volume'] = fetched_kdata['volume'].astype(np.float64)
            if fetched_kdata['position'].dtype != np.int64:
                fetched_kdata['position'] = fetched_kdata['position'].astype(np.int64)
            # for name in ('open','close','high','low')
            # fetched_kdata[]
            # 去除成交量为0的数据，包括停牌和因涨跌停造成无成交
            # fetched_kdata.drop(fetched_kdata[fetched_kdata['volume'] == 0].index, inplace=True)
            # fetched_kdata.reset_index(drop=True, inplace=True)
        return fetched_kdata

    @staticmethod
    @retry(stop_max_attempt_number=5)
    def fetch_codelist(socket_client, market=MarketType.Ashare):
        pass

    def fetch_latest_quotes(self, sock_client, code: object):
        pass


class DataSourceTdxLocal(DataSourceBase):
    name = 'tdx_local'
    sk_client = TdxStdReader

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
            return pd.DataFrame(columns=['time', 'open', 'close', 'high', 'low', 'volume'])
        else:
            try:
                df = store.get('_' + freq)
            except KeyError:
                print("未储存此frequency的数据:{}".format(freq))
                store.close()
                return pd.DataFrame(columns=['time', 'open', 'close', 'high', 'low', 'volume'])
            else:
                store.close()
                return df

    @staticmethod
    def get_codelist(reader, market=MarketType.Ashare):
        try:
            datapath = reader.find_path_codelist(market)
            code_list = pd.read_csv(datapath, encoding='utf-8', dtype={'code': str, 'name': str, 'market': int})
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['code', 'name', 'market'])
        else:
            return code_list

    @staticmethod
    def get_basic_finance_data(reader, market=MarketType.Ashare):
        try:
            datapath = reader.find_path_basic_finance_data(market)
            data_df = pd.read_csv(datapath, encoding='utf-8', dtype={'代码': str, '流通股本': float,
                                                                     '市盈率-动态': float, '市净率': float})
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=["代码", '流通股本', '市盈率-动态', "市净率"])
        else:
            return data_df

    @staticmethod
    def get_relativity_score_data(reader, market=MarketType.Ashare):
        try:
            fname = 'relativity_analyze_result.h5'
            datapath = reader.find_path_anaresult(fname)
            store = pd.HDFStore(datapath, mode='r', complib=HDF5_COMPLIB, complevel=HDF5_COMP_LEVEL)
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
        else:
            key = anadata_store_market_transform(market)
            try:
                df = store.get(key=key)
            except KeyError:
                print("未储存此市场的数据:{}".format(key))
                store.close()
                return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
            else:
                store.close()
                return df

    @staticmethod
    def get_blocks_score_data(reader, market=MarketType.Ashare):
        try:
            fname = 'blocks_score_analyze_result.h5'
            datapath = reader.find_path_anaresult(fname)
            store = pd.HDFStore(datapath, mode='r', complib=HDF5_COMPLIB, complevel=HDF5_COMP_LEVEL)
        except OSError as e:
            print(e)
            return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
        else:
            key = anadata_store_market_transform(market)
            try:
                df = store.get(key=key)
            except KeyError:
                print("未储存此市场的数据:{}".format(key))
                store.close()
                return pd.DataFrame(columns=['time', 'code', 'name', 'score'])
            else:
                store.close()
                return df

    @staticmethod
    def get_blocks_data(reader, market=MarketType.Ashare):
        try:
            datapath = reader.find_path_blocksdata(market)
        except OSError as e:
            print(e)
            return dict()
        else:
            with open(datapath, 'r') as f:
                res = json.load(f)
            return res


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
        market, market_type = kdata_store_market_transform(market)
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
        if self.localdir is None:
            raise RuntimeError("没有init socket")

        market_str = anadata_store_market_transform(market)
        path = Path('/'.join([self.localdir, 'code_list_' + market_str + '.csv']))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    def find_path_basic_finance_data(self, market):
        if self.localdir is None:
            raise RuntimeError("没有init socket")

        market_str = anadata_store_market_transform(market)
        path = Path('/'.join([self.localdir, 'AnalyzeData', market_str + '_basic_finance_data.csv']))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    def find_path_anaresult(self, fname):
        """
        自动匹配文件路径，辅助函数
        :return: path
        """
        if self.localdir is None:
            raise RuntimeError("没有init socket")

        path = Path('/'.join([self.localdir, 'AnalyzeData', fname]))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    def find_path_blocksdata(self, market):

        if self.localdir is None:
            raise RuntimeError("没有init socket")

        market_str = anadata_store_market_transform(market)
        path = Path('/'.join([self.localdir, market_str + '_blocks_data.json']))
        if not Path(path).exists():
            raise OSError(f'未找到所需的文件: {path}')
        return path

    def close(self):
        self.localdir = None


class DataSourceLocal(DataSourceBase):
    name = 'local'
    sk_client = LocalReader

    @staticmethod
    def fetch_kdata(socket_client, code) -> pd.DataFrame:
        fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                    code=code.code,
                                                    market=code.market,
                                                    freq=code.frequency.value)  # 这里要访问枚举类的value属性
        if len(fetched_kdata) == 0:
            return fetched_kdata
        out_df = fetched_kdata[(fetched_kdata['time'] >= code.start_time) &
                               (fetched_kdata['time'] <= code.end_time)]
        out_df.reset_index(drop=True, inplace=True)
        return out_df

    @staticmethod
    def fetch_codelist(socket_client, market) -> pd.DataFrame:
        codelist = socket_client.api.get_codelist(socket_client.socket,
                                                  market=market)

        return codelist[['code', 'name', 'market']]

    @staticmethod
    def fetch_basic_finance_data(socket_client, market) -> pd.DataFrame:
        data_df = socket_client.api.get_basic_finance_data(socket_client.socket,
                                                           market=market)

        return data_df

    @staticmethod
    def fetch_relativity_score_data(socket_client, market) -> pd.DataFrame:
        res_df = socket_client.api.get_relativity_score_data(socket_client.socket, market=market)
        return res_df

    @staticmethod
    def fetch_blocks_score_data(socket_client, market) -> pd.DataFrame:
        res_df = socket_client.api.get_blocks_score_data(socket_client.socket, market=market)
        return res_df

    @staticmethod
    def fetch_blocks_data(socket_client, market) -> dict:
        res_dict = socket_client.api.get_blocks_data(socket_client.socket, market=market)
        return res_dict


class RequestGenerater(object):
    remote_addr = None

    def __init__(self):
        self.socket = self
        self.api = RemoteServerAPI()

    def init_socket(self, remote_addr=REMOTE_ADDR):
        if requests.get(remote_addr).status_code == 200:
            self.remote_addr = remote_addr
        else:
            raise OSError('与远程服务器{} API测试连接错误！'.format(REMOTE_ADDR))
        return self

    def generate_kdata_url(self, code: str, freq: str, market: MarketType, st, et):
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
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")

        market_str = anadata_store_market_transform(market)
        get_url = self.remote_addr + '/codelist/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

    def generate_blocks_data_url(self, market):
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")
        market_str = anadata_store_market_transform(market)
        get_url = self.remote_addr + '/blockdata/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

    def generate_relativity_anadata_url(self, market):
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")
        market_str = anadata_store_market_transform(market)
        get_url = self.remote_addr + '/anadata/relativity/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

    def generate_blocks_score_data_url(self, market):
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")
        market_str = anadata_store_market_transform(market)
        get_url = self.remote_addr + '/anadata/blocksscore/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

    def generate_basic_finance_data_url(self, market):
        if self.remote_addr is None:
            raise RuntimeError("没有init socket")
        market_str = anadata_store_market_transform(market)
        get_url = self.remote_addr + '/financedata/basic/?'
        market_str = 'market=' + market_str
        get_url = get_url + market_str
        return get_url

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
            return JsonTool.getdata_from_json(kdata, orient='split')
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_codelist(req_generater, market=MarketType.Ashare):
        get_url = req_generater.generate_codelist_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            return JsonTool.getdata_from_json(data['data'], orient='split',
                                              dtype={'code': str, 'name': str, 'market': int})
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_blocks_data(req_generater, market=MarketType.Ashare):
        get_url = req_generater.generate_blocks_data_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            return json.loads(data['data'])
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_relativity_score_data(req_generater, market=MarketType.Ashare):
        get_url = req_generater.generate_relativity_anadata_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            content = data['data']
            return JsonTool.getdata_from_json(content, orient='split',
                                              dtype={'time': str, 'code': str, 'name': str, 'score': int})
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_blocks_score_data(req_generater, market=MarketType.Ashare):
        get_url = req_generater.generate_blocks_score_data_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            content = data['data']
            res = JsonTool.getdata_from_json(content, orient='split',
                                             dtype={'category': str, 'time': str, 'name': str,
                                                    'stk_count': int, 'score': float, 'rise_count': float})
            res['score'] = np.round(res['score'], 3)
            res['rise_count'] = np.round(res['rise_count'], 3)
            return res
        else:
            raise ValueError("VQapi返回msg 为 false")

    @staticmethod
    def get_basic_finance_data(req_generater, market=MarketType.Ashare):
        get_url = req_generater.generate_basic_finance_data_url(market=market)
        resp = requests.get(get_url).content
        data = json.loads(resp)
        if data['msg'] == 'success':
            return JsonTool.getdata_from_json(data['data'], orient='split',
                                              dtype={'代码': str, '流通股本': float,
                                                     '市盈率-动态': float, '市净率': float})
        else:
            raise ValueError("VQapi返回msg 为 false")


class DataSourceVQAPI(DataSourceBase):
    name = 'VQAPI'
    sk_client = RequestGenerater

    @staticmethod
    def fetch_kdata(socket_client, code):
        fetched_kdata = socket_client.api.get_kdata(socket_client.socket,
                                                    code=code.code,
                                                    freq=code.frequency.value,
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

    @staticmethod
    def fetch_basic_finance_data(socket_client, market) -> pd.DataFrame:
        data_df = socket_client.api.get_basic_finance_data(socket_client.socket,
                                                           market=market)

        return data_df

    @staticmethod
    def fetch_relativity_score_data(socket_client, market) -> pd.DataFrame:
        res_df = socket_client.api.get_relativity_score_data(socket_client.socket, market=market)
        return res_df

    @staticmethod
    def fetch_blocks_score_data(socket_client, market) -> pd.DataFrame:
        res_df = socket_client.api.get_blocks_score_data(socket_client.socket, market=market)
        return res_df

    @staticmethod
    def fetch_blocks_data(socket_client, market) -> dict:
        res_dict = socket_client.api.get_blocks_data(socket_client.socket, market=market)
        return res_dict


class AshareBasicDataAPI:
    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=100, wait_random_max=2000)
    def get_basic_finance_data() -> pd.DataFrame:
        """
        东方财富网-沪深京 A 股-实时行情
        http://quote.eastmoney.com/center/gridlist.html#hs_a_board
        :return: 实时行情
        :rtype: pandas.DataFrame
        """
        url = "http://82.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "5000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
            "_": "1623833739532",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，A股basic_finance数据获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            "_",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "换手率",
            "市盈率-动态",
            "量比",
            "_",
            "代码",
            "_",
            "名称",
            "最高",
            "最低",
            "今开",
            "昨收",
            "_",
            "_",
            "_",
            "市净率",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
        ]
        temp_df["换手率"] = pd.to_numeric(temp_df["换手率"], errors="coerce")
        temp_df["市盈率-动态"] = pd.to_numeric(temp_df["市盈率-动态"], errors="coerce")
        temp_df["市净率"] = pd.to_numeric(temp_df["市净率"], errors="coerce")
        temp_df[temp_df["换手率"] == 0] = 1  # 防止除0
        temp_df['流通股本'] = temp_df['成交量'] * 10000 / temp_df['换手率']
        res_df = temp_df[["代码", '流通股本', '市盈率-动态', "市净率"]]
        return res_df

    @staticmethod
    @retry(stop_max_attempt_number=3)
    def get_ashare_blocks_data() -> dict:
        res = {'按行业分类': dict(), '按概念分类': dict()}
        try:
            gn_names = AshareBasicDataAPI.get_gn_names_em()
            hy_names = AshareBasicDataAPI.get_hy_names_em()
            res['按概念分类']['0沪深京A股'] = AshareBasicDataAPI.get_all_cons_em()
        except Exception as e:
            logger.error("{} {}".format(e.__class__, e))
            raise FetchDataFailed("东方财富API调用失败，A股板块数据获取失败")
        else:
            try:
                for name, code in tqdm(zip(gn_names['板块名称'], gn_names['板块代码'])):
                    res['按概念分类'][name] = AshareBasicDataAPI.get_hy_cons_em(code)
                    time.sleep(0.5)
                time.sleep(0.5)
                for name, code in tqdm(zip(hy_names['板块名称'], hy_names['板块代码'])):
                    res['按行业分类'][name] = AshareBasicDataAPI.get_hy_cons_em(code)
                    time.sleep(0.5)
            except Exception as e:
                logger.error("{} {}".format(e.__class__, e))
                raise FetchDataFailed("东方财富API调用失败，A股板块数据获取失败")

        return res

    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_hy_names_em() -> pd.DataFrame:
        """
        东方财富网-沪深板块-行业板块-名称
        http://quote.eastmoney.com/center/boardlist.html#industry_board
        :return: 行业板块-名称
        :rtype: pandas.DataFrame
        """
        url = "http://17.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "2000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:90 t:2 f:!50",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f26,f22,f33,f11,f62,f128,f136,f115,f152,f124,f107,f104,f105,f140,f141,f207,f208,f209,f222",
            "_": "1626075887768",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，A股行业列表获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            '-',
            "最新价",
            "涨跌幅",
            "涨跌额",
            "-",
            "_",
            "-",
            "换手率",
            "-",
            "-",
            "-",
            "板块代码",
            "-",
            "板块名称",
            "-",
            "-",
            "-",
            "-",
            "总市值",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "-",
            "上涨家数",
            "下跌家数",
            "-",
            "-",
            "-",
            "领涨股票",
            "-",
            "-",
            "领涨股票-涨跌幅",
            "-",
            "-",
            "-",
            "-",
            "-",
        ]
        temp_df = temp_df[["板块名称", "板块代码"]]
        return temp_df

    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_hy_cons_em(symbol: str = "BK0475") -> list:
        """
        东方财富网-沪深板块-行业板块-板块成份
        https://data.eastmoney.com/bkzj/BK1027.html
        :param symbol: 板块名称
        :param code: 行业代码
        :type symbol: str
        :return: 板块成份
        :rtype: pandas.DataFrame
        """
        stock_board_code = symbol
        url = "http://29.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "2000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": f"b:{stock_board_code} f:!50",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45",
            "_": "1626081702127",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，A股行业详细数据获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            "_",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "换手率",
            "市盈率-动态",
            "_",
            "_",
            "代码",
            "_",
            "名称",
            "最高",
            "最低",
            "今开",
            "昨收",
            "_",
            "_",
            "_",
            "市净率",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
        ]
        res_list = temp_df["代码"].to_list()
        return res_list

    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_gn_names_em() -> pd.DataFrame:
        """
        东方财富网-沪深板块-概念板块-名称
        http://quote.eastmoney.com/center/boardlist.html#concept_board
        :return: 概念板块-名称
        :rtype: pandas.DataFrame
        """
        url = "http://79.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "2000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:90 t:3 f:!50",
            "fields": "f2,f3,f4,f8,f12,f14,f15,f16,f17,f18,f20,f21,f24,f25,f22,f33,f11,f62,f128,f124,f107,f104,f105,f136",
            "_": "1626075887768",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，A股概念列表获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            "最新价",
            "涨跌幅",
            "涨跌额",
            "换手率",
            "_",
            "板块代码",
            "板块名称",
            "_",
            "_",
            "_",
            "_",
            "总市值",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "上涨家数",
            "下跌家数",
            "_",
            "_",
            "领涨股票",
            "_",
            "_",
            "领涨股票-涨跌幅",
        ]
        temp_df = temp_df[["板块名称", "板块代码", ]]
        return temp_df

    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_gn_cons_em(symbol: str = "BK0816") -> list:
        """
        东方财富-沪深板块-概念板块-板块成份
        http://quote.eastmoney.com/center/boardlist.html#boards-BK06551
        :param symbol: 板块代码
        :type symbol: str
        :return: 板块成份
        :rtype: pandas.DataFrame
        """
        stock_board_code = symbol
        url = "http://29.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "2000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": f"b:{stock_board_code} f:!50",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152,f45",
            "_": "1626081702127",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，A股概念详细数据获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            "_",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "换手率",
            "市盈率-动态",
            "_",
            "_",
            "代码",
            "_",
            "名称",
            "最高",
            "最低",
            "今开",
            "昨收",
            "_",
            "_",
            "_",
            "市净率",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
        ]
        res_list = temp_df["代码"].to_list()
        return res_list

    @staticmethod
    @retry(stop_max_attempt_number=3, wait_random_min=1000, wait_random_max=2000)
    def get_all_cons_em() -> list:
        """
        东方财富网-沪深京 A 股-实时行情
        http://quote.eastmoney.com/center/gridlist.html#hs_a_board
        :return: 实时行情
        :rtype: pandas.DataFrame
        """
        url = "http://82.push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "5000",
            "po": "1",
            "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": "m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
            "_": "1623833739532",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        if not data_json["data"]["diff"]:
            raise FetchDataFailed("东方财富API调用失败，沪深京A股列表数据获取失败")
        temp_df = pd.DataFrame(data_json["data"]["diff"])
        temp_df.columns = [
            "_",
            "最新价",
            "涨跌幅",
            "涨跌额",
            "成交量",
            "成交额",
            "振幅",
            "换手率",
            "市盈率-动态",
            "量比",
            "_",
            "代码",
            "_",
            "名称",
            "最高",
            "最低",
            "今开",
            "昨收",
            "_",
            "_",
            "_",
            "市净率",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
            "_",
        ]
        res = temp_df["代码"].to_list()
        return res


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


class DataSource(object):
    """
    数据获取方法
    """

    class Local:
        VQtdx = DataSourceTdxLocal
        VQapi = DataSourceVQAPI
        Default = DataSourceLocal

    class Live:
        VQtdx = DataSourceTdxLive
        VQtdx_Ext = DataSourceExtTdxLive
        VQapi = DataSourceVQAPI


"""
默认数据获取方法
"""
#  默认本地A股K线数据获取方法
if ASHARE_LOCAL_DATASOURCE == 'Default':
    DEFAULT_ASHARE_LOCAL_DATASOURCE = DataSource.Local.Default
elif ASHARE_LOCAL_DATASOURCE == 'VQapi':
    DEFAULT_ASHARE_LOCAL_DATASOURCE = DataSource.Local.VQapi
elif ASHARE_LOCAL_DATASOURCE == 'VQtdx':
    DEFAULT_ASHARE_LOCAL_DATASOURCE = DataSource.Local.VQtdx
else:
    DEFAULT_ASHARE_LOCAL_DATASOURCE = DataSource.Local.Default

DEFAULT_FUTURE_LOCAL_DATASOURCE = DataSource.Local.Default
#  默认实时A股K线数据获取方法
if ASHARE_LIVE_DATASOURCE == 'VQtdx':
    DEFAULT_ASHARE_LIVE_DATASOURCE = DataSource.Live.VQtdx
elif ASHARE_LIVE_DATASOURCE == 'VQapi':
    DEFAULT_ASHARE_LIVE_DATASOURCE = DataSource.Live.VQapi
else:
    DEFAULT_ASHARE_LIVE_DATASOURCE = DataSource.Live.VQtdx
DEFAULT_FUTURE_LIVE_DATASOURCE = DataSource.Live.VQtdx_Ext

DEFAULT_ASHARE_DATA_SOURCE = {'local': DEFAULT_ASHARE_LOCAL_DATASOURCE, 'live': DEFAULT_ASHARE_LIVE_DATASOURCE}

#  默认代码列表数据获取方法
if CODELIST_DATASOURCE == 'Default':
    DEFAULT_CODELIST_DATASOURCE = DataSource.Local.Default
elif CODELIST_DATASOURCE == 'VQapi':
    DEFAULT_CODELIST_DATASOURCE = DataSource.Local.VQapi
elif CODELIST_DATASOURCE == 'VQtdx':
    DEFAULT_CODELIST_DATASOURCE = DataSource.Local.VQtdx
else:
    DEFAULT_CODELIST_DATASOURCE = DataSource.Local.Default

#  默认板块数据获取方法
if BLOCKS_DATA_DATASOURCE == 'Default':
    DEFAULT_BLOCKS_DATA_DATASOURCE = DataSource.Local.Default
elif BLOCKS_DATA_DATASOURCE == 'VQapi':
    DEFAULT_BLOCKS_DATA_DATASOURCE = DataSource.Local.VQapi
elif BLOCKS_DATA_DATASOURCE == 'VQtdx':
    DEFAULT_BLOCKS_DATA_DATASOURCE = DataSource.Local.VQtdx
else:
    DEFAULT_BLOCKS_DATA_DATASOURCE = DataSource.Local.Default

#  默认基本经济数据获取方法
if BASIC_FINANCE_DATA_DATASOURCE == 'Default':
    DEFAULT_BASIC_FINANCE_DATA_DATASOURCE = DataSource.Local.Default
elif BASIC_FINANCE_DATA_DATASOURCE == 'VQapi':
    DEFAULT_BASIC_FINANCE_DATA_DATASOURCE = DataSource.Local.VQapi
else:
    DEFAULT_BASIC_FINANCE_DATA_DATASOURCE = DataSource.Local.Default

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
    # store_code_list_stock(test_stock_list, Market.Ashare)

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
    # test_stock_list_local = new_test_code.data_source_local.fetch_codelist(test_socket_client_local, Market.Ashare)
    # print(test_stock_list_local)

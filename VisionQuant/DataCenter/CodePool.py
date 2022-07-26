from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DataSource, DEFAULT_ASHARE_DATA_SOURCE, DEFAULT_CODELIST_DATASOURCE, \
    DEFAULT_BLOCKS_DATA_DATASOURCE
from VisionQuant.utils.Params import MarketType
from VisionQuant.utils.VQlog import logger
from pandas.core.series import Series


class CodePool:
    def __init__(self, codelist_data_source=None, blocks_data_source=None):
        self.code_df = None
        self.codelist_data_source = codelist_data_source
        self.blocks_data_source = blocks_data_source

    def get_code(self, codes, start_time=None, end_time=None, frequency=None):
        raise NotImplementedError("没有重写该方法")

    def get_all_code(self, start_time=None, end_time=None, frequency=None):
        raise NotImplementedError("没有重写该方法")


class FutureCodePool(CodePool):

    def __init__(self, codelist_data_source=DEFAULT_CODELIST_DATASOURCE):
        super().__init__(codelist_data_source)

    def get_code(self, code, start_time=None, end_time=None, frequency=None, **kwargs):
        if self.code_df is None:
            self.get_code_df()
        if isinstance(code, str):
            res = Code(code=code,
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, **kwargs)
            name = self.code_df[(self.code_df['code'] == res.code) &
                                (self.code_df['market'] == res.market.value)].name.values[0]
            res.name = name
            # if not isinstance(code_line, Series):
            #     code_line = code_line.to_dict(orient='records')[0]
            return res
        elif isinstance(code, tuple):
            _code, market = code
            res = Code(code=_code,
                       market=market,
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, **kwargs)
            name = self.code_df[(self.code_df['code'] == res.code) &
                                (self.code_df['market'] == res.market.value)].name.values[0]
            res.name = name
            return res
        else:
            logger.critical("错误的code参数类型!")
            raise ValueError("错误的code参数类型!")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, return_type=dict, selected_market=None,
                     **kwargs):
        if self.code_df is None:
            self.get_code_df()
        if return_type == dict:
            codedict = dict()
            for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                       end_time=end_time, frequency=frequency, **kwargs)
            return codedict
        else:
            codelist = []
            if selected_market is None:
                for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                    codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time,
                                         end_time=end_time, frequency=frequency, **kwargs))
                return codelist
            else:
                values = [x.value for x in selected_market]
                for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                    if _market in values:
                        codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time,
                                             end_time=end_time, frequency=frequency, **kwargs))
                return codelist

    def get_code_df(self):
        sk = self.codelist_data_source.sk_client().init_socket()
        try:
            data = self.codelist_data_source.fetch_codelist(sk, market=MarketType.Future).set_index('code', drop=False)
        except Exception as e:
            logger.error("获取code_df失败，详细信息: {}{}".format(e.__class__, e))
            raise RuntimeError('获取code_df失败')
        else:
            self.code_df = data
        finally:
            sk.close()


class AshareCodePool(CodePool):

    def __init__(self, codelist_data_source=DEFAULT_CODELIST_DATASOURCE,
                 blocks_data_source=DEFAULT_BLOCKS_DATA_DATASOURCE):
        super().__init__(codelist_data_source, blocks_data_source)
        self.blocks_data = None

    def get_code(self, code, start_time=None, end_time=None, frequency=None, **kwargs):
        if self.code_df is None:
            self.get_code_df()
        if isinstance(code, str):
            res = Code(code=code,
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, **kwargs)
            name = self.code_df[(self.code_df['code'] == res.code) &
                                (self.code_df['market'] == res.market.value)].name.values[0]
            res.name = name
            # if not isinstance(code_line, Series):
            #     code_line = code_line.to_dict(orient='records')[0]
            return res
        elif isinstance(code, tuple):
            _code, market = code
            res = Code(code=_code,
                       market=market,
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, **kwargs)
            name = self.code_df[(self.code_df['code'] == res.code) &
                                (self.code_df['market'] == res.market.value)].name.values[0]
            res.name = name
            return res
        else:
            logger.critical("错误的code参数类型!")
            raise ValueError("错误的code参数类型!")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, return_type=dict, selected_market=None,
                     **kwargs):
        if self.code_df is None:
            self.get_code_df()
        if return_type == dict:
            codedict = dict()
            for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                if _code in codedict:
                    if _market in (MarketType.Ashare.SH.STOCK, MarketType.Ashare.SZ.STOCK,
                                   MarketType.Ashare.SH.KCB, MarketType.Ashare.SZ.CYB):
                        codedict[_code] = Code(code=_code, name=_name, market=_market,
                                               start_time=start_time, end_time=end_time, frequency=frequency, **kwargs)
                    else:
                        continue
                else:
                    codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                           end_time=end_time, frequency=frequency, **kwargs)
            return codedict
        else:
            codelist = []
            if selected_market is None:
                for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                    codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time,
                                         end_time=end_time, frequency=frequency, **kwargs))
                return codelist
            else:
                values = [x.value for x in selected_market]
                for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                    if _market in values:
                        codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time,
                                             end_time=end_time, frequency=frequency, **kwargs))
                return codelist

    def get_blocks_data(self, key=None):
        if self.blocks_data is None:
            self._get_blocks_data()
        if key is None:
            return self.blocks_data
        elif key not in self.blocks_data.keys():
            logger.error("错误的A股板块类型")
            return self.blocks_data
        else:
            return self.blocks_data[key]

    def get_code_df(self):
        sk = self.codelist_data_source.sk_client().init_socket()
        try:
            data = self.codelist_data_source.fetch_codelist(sk, market=MarketType.Ashare).set_index('code', drop=False)
        except Exception as e:
            logger.error("获取code_df失败，详细信息: {}{}".format(e.__class__, e))
            raise RuntimeError('获取code_df失败')
        else:
            self.code_df = data
        finally:
            sk.close()

    def _get_blocks_data(self):
        sk = self.blocks_data_source.sk_client().init_socket()
        try:
            data = self.blocks_data_source.fetch_blocks_data(sk, market=MarketType.Ashare)
        except Exception as e:
            logger.error("获取blocks_data失败，详细信息: {}{}".format(e.__class__, e))
            raise RuntimeError('获取blocks_data失败')
        else:
            self.blocks_data = data
        finally:
            sk.close()
        self.blocks_data = data


if __name__ == '__main__':
    # print(get_ashare_stock_list())
    # test_pool = AshareCodePool()
    # test_list = ['999999', '600519', '399006', ('000688', MarketType.Ashare.SH.INDEX)]
    test_pool = FutureCodePool()
    test_list = ['RBL8', 'FGL8', 'LHL8', 'ICL8', 'BCL8']
    test_code_list = []
    for test_code in test_list:
        test_code_list.append(test_pool.get_code(test_code))
    # test_all_code_list = test_pool.get_all_code(return_type=list)
    for _code in test_code_list:
        print(_code.code, _code.name, _code.market)
    # test_codedict = test_pool.get_code(['999999', '600519', '399006', ('000688', MarketType.Ashare.SH.INDEX)])
    # for test_code in test_codedict.values():
    #     print(test_code.code, test_code.name, test_code.market)
    # test_code = test_pool.get_code(('000688', MarketType.Ashare.SZ.STOCK))
    # print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    # test_code = test_pool.get_code('000688')
    # print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    # test_code_dict = test_pool.get_all_code()
    # print(test_code_dict['000688'].name)
    # for test_code in test_code_dict.values():
    #     print(test_code.code, test_code.name, test_code.market)

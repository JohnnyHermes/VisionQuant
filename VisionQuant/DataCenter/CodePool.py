from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DataSource
from VisionQuant.utils.Params import Market, DEFAULT_ASHARE_LOCAL_DATASOURCE, DEFAULT_ASHARE_LIVE_DATASOURCE
from VisionQuant.utils.VQlog import logger
from pandas.core.series import Series

if DEFAULT_ASHARE_LOCAL_DATASOURCE == 'Default':
    ashare_local_source = DataSource.Local.Default
elif DEFAULT_ASHARE_LOCAL_DATASOURCE == 'VQapi':
    ashare_local_source = DataSource.Local.VQapi
elif DEFAULT_ASHARE_LOCAL_DATASOURCE == 'VQtdx':
    ashare_local_source = DataSource.Local.VQtdx
else:
    ashare_local_source = DataSource.Local.Default

if DEFAULT_ASHARE_LIVE_DATASOURCE == 'VQtdx':
    ashare_live_source = DataSource.Live.VQtdx
elif DEFAULT_ASHARE_LIVE_DATASOURCE == 'VQapi':
    ashare_live_source = DataSource.Live.VQapi
else:
    ashare_live_source = DataSource.Live.VQtdx

DEFAULT_ASHARE_DATA_SOURCE = {'local': ashare_local_source, 'live': ashare_live_source}


class CodePool:
    def __init__(self, codelist_data_source=None, blocks_data_source=None, code_default_data_source=None):
        self.code_df = None
        self.codelist_data_source = codelist_data_source
        self.blocks_data_source = blocks_data_source
        self.default_data_source = code_default_data_source

    def get_code(self, codes: list, start_time=None, end_time=None, frequency=None, data_source=None):
        raise NotImplementedError("没有重写该方法")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, data_source=None):
        raise NotImplementedError("没有重写该方法")


class AshareCodePool(CodePool):

    def __init__(self, codelist_data_source=DataSource.Local.Default, blocks_data_source=DataSource.Local.Default,
                 code_default_data_source=None):
        if code_default_data_source is None:
            code_default_data_source = DEFAULT_ASHARE_DATA_SOURCE
        super().__init__(codelist_data_source, blocks_data_source, code_default_data_source)
        self.blocks_data = None

    def get_code(self, code, start_time=None, end_time=None, frequency=None, data_source=None):
        if self.code_df is None:
            self.get_code_df()
        if data_source is None:
            data_source = self.default_data_source
        if isinstance(code, list):
            codedict = dict()
            for item in code:
                if isinstance(item, str):
                    _code = item
                    code_line = self.code_df.loc[_code]
                    if not isinstance(code_line, Series):
                        code_line = code_line.to_dict(orient='records')[0]
                elif isinstance(item, tuple):
                    _code, market = item
                    code_line = self.code_df.loc[_code]
                    code_line = code_line[code_line['market'] == market].to_dict(orient='records')[0]
                else:
                    logger.critical("错误的code item参数类型!")
                    raise ValueError("错误的code item参数类型!")
                codedict[_code] = Code(code=code_line['code'],
                                       name=code_line['name'],
                                       market=code_line['market'],
                                       start_time=start_time, end_time=end_time,
                                       frequency=frequency, data_source=data_source)
            return codedict
        elif isinstance(code, str):
            code_line = self.code_df.loc[code]
            if not isinstance(code_line, Series):
                code_line = code_line.to_dict(orient='records')[0]
            res = Code(code=code_line['code'],
                       name=code_line['name'],
                       market=code_line['market'],
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, data_source=data_source)
            return res
        elif isinstance(code, tuple):
            _code, market = code
            code_line = self.code_df.loc[_code]
            code_line = code_line[code_line['market'] == market].to_dict(orient='records')[0]
            res = Code(code=code_line['code'],
                       name=code_line['name'],
                       market=code_line['market'],
                       start_time=start_time, end_time=end_time,
                       frequency=frequency, data_source=data_source)
            return res
        else:
            logger.critical("错误的code参数类型!")
            raise ValueError("错误的code参数类型!")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, data_source=None, return_type=dict):
        if self.code_df is None:
            self.get_code_df()
        if data_source is None:
            data_source = self.default_data_source
        if return_type == dict:
            codedict = dict()
            for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                if _code in codedict:
                    if _market in (Market.Ashare.MarketSH.STOCK, Market.Ashare.MarketSZ.STOCK,
                                   Market.Ashare.MarketSH.KCB, Market.Ashare.MarketSZ.CYB):
                        codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                               end_time=end_time, frequency=frequency, data_source=data_source)
                    else:
                        continue
                else:
                    codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                           end_time=end_time, frequency=frequency, data_source=data_source)
            return codedict
        else:
            codelist = []
            for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
                codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time,
                                     end_time=end_time, frequency=frequency, data_source=data_source))
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
            data = self.codelist_data_source.fetch_codelist(sk, market=Market.Ashare).set_index('code', drop=False)
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
            data = self.blocks_data_source.fetch_blocks_data(sk, market=Market.Ashare)
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
    test_pool = AshareCodePool(DataSource.Local.VQapi)
    test_codedict = test_pool.get_code(['999999', '600519', '399006', ('000688', Market.Ashare.MarketSH.INDEX)])
    for test_code in test_codedict.values():
        print(test_code.code, test_code.name, test_code.market)
    test_code = test_pool.get_code(('000688', Market.Ashare.MarketSZ.STOCK))
    print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    test_code = test_pool.get_code('000688')
    print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    test_code_dict = test_pool.get_all_code()
    print(test_code_dict['000688'].name)
    # for test_code in test_code_dict.values():
    #     print(test_code.code, test_code.name, test_code.market)

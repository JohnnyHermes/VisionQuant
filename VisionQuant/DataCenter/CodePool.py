from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DataSource, SocketClientsManager
from VisionQuant.utils.Params import Stock
from pandas.core.series import Series

DEFAULT_ASHARE_DATA_SOURCE = {'local': DataSource.Local.VQapi, 'live': DataSource.Live.VQapi}


class CodePool:
    def __init__(self, code_default_data_source=None):
        self.code_df = None
        self.default_data_source = code_default_data_source

    def get_code(self, codes: list, start_time=None, end_time=None, frequency=None, data_source=None):
        raise NotImplementedError("没有重写该方法")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, data_source=None):
        raise NotImplementedError("没有重写该方法")


class AshareCodePool(CodePool):

    def __init__(self, codelist_data_source=DataSource.Local.VQapi, code_default_data_source=None):
        if code_default_data_source is None:
            code_default_data_source = DEFAULT_ASHARE_DATA_SOURCE
        super().__init__(code_default_data_source)
        sk = codelist_data_source.name[1]().init_socket()
        self.code_df = codelist_data_source.fetch_codelist(sk, market=Stock.Ashare).set_index('code', drop=False)

    def get_code(self, code, start_time=None, end_time=None, frequency=None, data_source=None):
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
                    raise ValueError("get_ashare_stock_list: 错误的code类型")
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
            raise ValueError("错误参数输入: code")

    def get_all_code(self, start_time=None, end_time=None, frequency=None, data_source=None):
        if data_source is None:
            data_source = self.default_data_source
        codedict = dict()
        for _code, _name, _market in zip(self.code_df['code'], self.code_df['name'], self.code_df['market']):
            if _code in codedict:
                if _market in (Stock.Ashare.MarketSH.STOCK, Stock.Ashare.MarketSZ.STOCK,
                               Stock.Ashare.MarketSH.KCB, Stock.Ashare.MarketSZ.CYB):
                    codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                           end_time=end_time, frequency=frequency, data_source=data_source)
                else:
                    continue
            else:
                codedict[_code] = Code(code=_code, name=_name, market=_market, start_time=start_time,
                                       end_time=end_time, frequency=frequency, data_source=data_source)
        return codedict


if __name__ == '__main__':
    # print(get_ashare_stock_list())
    test_pool = AshareCodePool(DataSource.Local.VQapi)
    test_codedict = test_pool.get_code(['999999', '600519', '399006', ('000688', Stock.Ashare.MarketSH.INDEX)])
    for test_code in test_codedict.values():
        print(test_code.code, test_code.name, test_code.market)
    test_code = test_pool.get_code(('000688', Stock.Ashare.MarketSZ.STOCK))
    print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    test_code = test_pool.get_code('000688')
    print(test_code.code, test_code.name, test_code.market, test_code.start_time, test_code.end_time)
    test_code_dict = test_pool.get_all_code()
    print(test_code_dict['000688'].name)
    # for test_code in test_code_dict.values():
    #     print(test_code.code, test_code.name, test_code.market)

from VisionQuant.utils.Code import Code
from VisionQuant.DataCenter.DataFetch import DataSource, SocketClientsManager
from VisionQuant.utils.Params import Stock

sk_client_mng = SocketClientsManager()


def get_ashare_stock_list(codes: list = None, start_time=None, end_time=None, frequency=None, data_source=None):
    codelist = []
    sk = sk_client_mng.init_socket(*DataSource.Local.Default.name)
    ashare_codelist = DataSource.Local.Default.fetch_codelist(sk, market=Stock.Ashare)
    if codes is None:
        for _code, _name, _market in zip(ashare_codelist['code'], ashare_codelist['name'], ashare_codelist['market']):
            codelist.append(Code(code=_code, name=_name, market=_market, start_time=start_time, end_time=end_time,
                                 frequency=frequency, data_source=data_source))

        return codelist
    else:
        for code in codes:
            if isinstance(code, str):
                code_line = ashare_codelist[ashare_codelist['code'] == code]
            elif isinstance(code, tuple):
                code, market = code
                code_line = ashare_codelist[ashare_codelist['code'] == code]
                code_line = code_line[code_line['market'] == market]
            else:
                raise ValueError("get_ashare_stock_list: 错误的code类型")
            codelist.append(Code(code=code_line['code'].values[0],
                                 name=code_line['name'].values[0],
                                 market=code_line['market'].values[0],
                                 start_time=start_time, end_time=end_time,
                                 frequency=frequency, data_source=data_source))
        return codelist


if __name__ == '__main__':
    # print(get_ashare_stock_list())
    test_codelist = get_ashare_stock_list(['002382', ('000688', Stock.Ashare.MarketSH.INDEX)])
    for test_code in test_codelist:
        print(test_code.code, test_code.name, test_code.market)

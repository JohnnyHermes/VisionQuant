from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import Stock, Freq
import copy


def determine_market(code: str, selected_market=None):
    """
        判断股票ID对应的证券市场匹配规则
        ['88']开头的为上海指数
        '999999'为上证指数
        '000'开头且index在1000前的是指数
        ['01','02','10','11','12','13','14','15','16','17','18']开头为债
        '11','12'开头为可转债
        '20'，'36'开头没用
        ['50','51']开头是ETF
        ['52','56','58']没用
        ['60']开头是上海A股index14800
        ['75','76','77','78','79']开头没用
        ['90','93']开头没用
        
        sz
        ['39']开头的为深圳指数
        ['00']开头为深圳A股
        ['159']开头为深圳ETF
        ['16','18']开头为深圳基金
        ['19']开头为国债
        ['20']开头为B股
        ['30']开头为创业板

        'sh' = '00'指数, '11'可转债, '50'场外基金, ['51','58']场内ETF, '60'上海A股, '68'科创板
               '8802'地域板块指数, ['8803','8804']行业板块指数(56个), ['8805'~'8809']概念、风格板块
               '999997'B股指数, '999998'A股指数, '999999'上证指数
        'sz' = '00'深圳A股, '12'可转债, '15'场内ETF, '16'场外基金 '30'创业板,
               '39'指数
               '399001'深圳成指, '399006'创业板指, '399905'中证500
        重要指数: '999999'上证指数  '000688'科创50 '000300'沪深300 '000016'上证50 '000011'上海ETF指数
                 '399001'深圳成指 '399006'创业板指 '399905'中证500 '399673'创业板50 '399306'深圳ETF指数
        :param selected_market: 当market参数为None时，默认不知道代码属于哪个市场，因此A股'00'将被认为是深A
        :param code:
        :return market_type
    """

    ch = code[0:2]

    if selected_market is Stock.Ashare.MarketSH:
        if ch == '60':
            return Stock.Ashare.MarketSH.STOCK
        elif ch == '68':
            return Stock.Ashare.MarketSH.KCB
        elif ch == '88':
            return Stock.Ashare.MarketSH.INDEX
        elif code in ['000688', '000300', '000016', '000011', '999999']:
            return Stock.Ashare.MarketSH.INDEX
        elif ch in ['51', '58']:
            return Stock.Ashare.MarketSH.ETF
        elif ch == '11':
            return Stock.Ashare.MarketSH.BOND
        else:
            return Stock.Ashare.MarketSH.OTHERS
    elif selected_market is Stock.Ashare.MarketSZ:
        if ch == '00':
            return Stock.Ashare.MarketSZ.STOCK
        elif ch == '30':
            return Stock.Ashare.MarketSZ.CYB
        elif code in ['399001', '399006', '399905', '399673', '399306']:
            return Stock.Ashare.MarketSZ.INDEX
        elif ch == '15':
            return Stock.Ashare.MarketSZ.ETF
        elif ch == '12':
            return Stock.Ashare.MarketSZ.BOND
        else:
            return Stock.Ashare.MarketSZ.OTHERS
    else:
        if ch == '60':
            return Stock.Ashare.MarketSH.STOCK
        elif ch == '00':
            return Stock.Ashare.MarketSZ.STOCK
        elif ch == '30':
            return Stock.Ashare.MarketSZ.CYB
        elif ch == '68':
            return Stock.Ashare.MarketSH.KCB
        elif ch in ['00', '88']:
            return Stock.Ashare.MarketSH.INDEX
        elif ch == '39':
            return Stock.Ashare.MarketSZ.INDEX
        elif ch in ['51', '58']:
            return Stock.Ashare.MarketSH.ETF
        elif ch == '15':
            return Stock.Ashare.MarketSZ.ETF
        elif ch == '11':
            return Stock.Ashare.MarketSH.BOND
        elif ch == '12':
            return Stock.Ashare.MarketSZ.BOND
        elif code == '999999':
            return Stock.Ashare.MarketSH.INDEX
        else:
            return Stock.Ashare.MarketSH.OTHERS


def code_transform(code: str):
    if isinstance(code, str):
        # 聚宽股票代码格式 '600000.XSHG'
        # 掘金股票代码格式 'SHSE.600000'
        # Wind股票代码格式 '600000.SH'
        # 天软股票代码格式 'SH600000'
        if len(code) == 6:
            return code
        if len(code) == 9:
            tmp = code.split(".")
            if len(tmp[0]) == 6:
                return tmp[0]
            else:
                return tmp[1]
        if len(code) == 11:
            if code[0] in ["S"]:
                return code.split(".")[1]
            return code.split(".")[0]
        raise ValueError("错误的股票代码格式")
    else:
        raise ValueError("错误的股票代码格式，代码不是string格式")


class Code:
    def __init__(self, code, frequency=None, start_time=None, end_time=None,
                 data_source: dict = None, name=None, market=None):
        self.code = code_transform(code)
        if name is not None:
            self.name = name
        else:
            self.name = 'null'
        if market is not None:
            self.market = market
        else:
            self.market = determine_market(code)
        if frequency is not None:
            self.frequency = frequency
        else:
            self.frequency = Freq.MIN5
        if start_time is not None:
            self.start_time = TimeTool.time_standardization(start_time)
        else:
            self.start_time = TimeTool.time_standardization('2015-1-1')
        if end_time is not None:
            self.end_time = TimeTool.time_standardization(end_time)
        else:
            self.end_time = TimeTool.get_now_time()
        if data_source is not None:
            if 'local' in data_source:
                self.data_source_local = data_source['local']
            else:
                from VisionQuant.DataCenter.DataFetch import DataSource
                self.data_source_local = DataSource.Local.VQtdx
            if 'live' in data_source:
                self.data_source_live = data_source['live']
            else:
                from VisionQuant.DataCenter.DataFetch import DataSource
                self.data_source_live = DataSource.Live.VQtdx
        else:
            from VisionQuant.DataCenter.DataFetch import DataSource
            self.data_source_local = DataSource.Local.Default
            self.data_source_live = DataSource.Live.VQtdx

    def copy(self):
        return copy.deepcopy(self)


if __name__ == '__main__':
    cod = Code('600001')
    cod1 = cod.copy()
    print(cod)
    print(cod1)
    from VisionQuant.DataCenter.DataFetch import DataSource

    cod1.data_source_local = DataSource.Local.Default
    print(cod.data_source_local)
    print(cod1.data_source_local)

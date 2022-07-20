from VisionQuant.utils import TimeTool
from VisionQuant.utils.Params import MarketType, Freq
from typing import Union
import copy


def determine_market(code: str, selected_market=None, return_type=MarketType):
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
        :param return_type:
        :param selected_market: 当market参数为None时，默认不知道代码属于哪个市场，因此A股'00'将被认为是深A
        :param code:
        :return market_type
    """

    ch = code[0:2]
    if selected_market is MarketType.Ashare.SH:
        if ch == '60':
            res = MarketType.Ashare.SH.STOCK
        elif ch == '68':
            res = MarketType.Ashare.SH.KCB
        elif ch == '88':
            res = MarketType.Ashare.SH.INDEX
        elif code in ['000688', '000300', '000016', '000011', '999999']:
            res = MarketType.Ashare.SH.INDEX
        elif ch in ['51', '58']:
            res = MarketType.Ashare.SH.ETF
        elif ch == '11':
            res = MarketType.Ashare.SH.BOND
        else:
            res = MarketType.Ashare.SH.OTHERS
    elif selected_market is MarketType.Ashare.SZ:
        if ch == '00':
            res = MarketType.Ashare.SZ.STOCK
        elif ch == '30':
            res = MarketType.Ashare.SZ.CYB
        elif code in ['399001', '399006', '399905', '399673', '399306']:
            res = MarketType.Ashare.SZ.INDEX
        elif ch == '15':
            res = MarketType.Ashare.SZ.ETF
        elif ch == '12':
            res = MarketType.Ashare.SZ.BOND
        else:
            res = MarketType.Ashare.SZ.OTHERS
    elif selected_market is MarketType.Future:
        ch = code[:2]
        if ch[1] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') or len(code) in (3, 5):
            if ch[0] in ('A', 'B', 'C', 'I', 'J', 'L', 'M', 'P', 'V', 'Y'):
                res = MarketType.Future.DS
            elif ch[0] == 'T':
                res = MarketType.Future.ZJ
        elif ch in ('IC', 'IF', 'IH', 'TF', 'T', 'TS'):
            res = MarketType.Future.ZJ
        elif ch in ('AP', 'CF', 'CJ', 'CY', 'FG', 'JR', 'LR', 'MA', 'OI', 'PF', 'PK', 'PM',
                    'RI', 'RM', 'RS', 'SA', 'SF', 'SM', 'SR', 'TA', 'UR', 'WH', 'ZC'):
            res = MarketType.Future.ZS
        elif ch in ('A', 'BB', 'B', 'C', 'CS', 'EB', 'EG', 'FB', 'I', 'JD', 'J', 'JM', 'LH',
                    'L', 'M', 'PG', 'P', 'PP', 'RR', 'V', 'Y'):
            res = MarketType.Future.DS
        elif ch in ('AG', 'AL', 'AU', 'BC', 'BU', 'CU', 'FU', 'HC', 'LU', 'NI', 'NR', 'PB',
                    'RB', 'RU', 'SC', 'SN', 'SP', 'SS', 'WR', 'ZN'):
            res = MarketType.Future.SQ
        else:
            raise ValueError("错误的代码")
    else:
        if ch == '60':
            res = MarketType.Ashare.SH.STOCK
        elif ch == '00':
            res = MarketType.Ashare.SZ.STOCK
        elif ch == '30':
            res = MarketType.Ashare.SZ.CYB
        elif ch == '68':
            res = MarketType.Ashare.SH.KCB
        elif ch in ['00', '88']:
            res = MarketType.Ashare.SH.INDEX
        elif ch == '39':
            res = MarketType.Ashare.SZ.INDEX
        elif ch in ['51', '58']:
            res = MarketType.Ashare.SH.ETF
        elif ch == '15':
            res = MarketType.Ashare.SZ.ETF
        elif ch == '11':
            res = MarketType.Ashare.SH.BOND
        elif ch == '12':
            res = MarketType.Ashare.SZ.BOND
        elif code == '999999':
            res = MarketType.Ashare.SH.INDEX
        else:
            res = MarketType.Ashare.SH.OTHERS

    if return_type == MarketType:
        return res
    else:
        return res.value


def select_markettype(i):
    if i < 10:
        if i % 2 == 0:
            return MarketType.Ashare.SH(i)
        else:
            return MarketType.Ashare.SZ(i)
    elif i == 10:
        return MarketType.Ashare.SH.OTHERS
    elif i == 11:
        return MarketType.Ashare.BJ.STOCK
    elif i == 29:
        return MarketType.Future.DS
    elif i == 28:
        return MarketType.Future.ZS
    elif i == 30:
        return MarketType.Future.SQ
    elif i == 47:
        return MarketType.Future.ZJ
    else:
        raise ValueError


def market_str_transform(market_str):
    if market_str in ['sh', 'SH']:
        return MarketType.Ashare.SH
    elif market_str in ['sz', 'SZ']:
        return MarketType.Ashare.SZ


def code_transform(code: str):
    if isinstance(code, str):
        # 聚宽股票代码格式 '600000.XSHG'
        # 掘金股票代码格式 'SHSE.600000'
        # Wind股票代码格式 '600000.SH'
        # 天软股票代码格式 'SH600000'
        if len(code) < 6:
            return code, MarketType.Future
        if len(code) == 6:
            if code[0] not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
                return code, MarketType.Future
            return code, None
        if len(code) == 9:
            tmp = code.split(".")
            if len(tmp[0]) == 6:
                return tmp[0], market_str_transform(tmp[1])
            else:
                return tmp[1], market_str_transform(tmp[0])
        if len(code) == 11:
            if code[0] in ["S"]:
                return code.split(".")[1]
            return code.split(".")[0]
        raise ValueError("错误的股票代码格式")
    else:
        raise ValueError("错误的股票代码格式，代码不是string格式")


class Code:
    def __init__(self, code: str, name: str = None, market: Union[MarketType, int] = None, frequency=None,
                 start_time=None, end_time=None):
        self.code, _market = code_transform(code)
        if name is not None:
            self.name = name
        else:
            self.name = 'null'
        if market is not None:
            if isinstance(market, int):
                self.market = select_markettype(market)
            else:
                self.market = market
        else:
            self.market = determine_market(self.code, _market)
        if frequency is not None:
            if isinstance(frequency, list):
                res = []
                for freq in frequency:
                    if isinstance(freq, str):
                        res.append(Freq(freq))
                    elif isinstance(freq, Freq):
                        res.append(freq)
                    else:
                        raise ValueError("错误的Frequency类型")
                self.frequency = res
            else:
                if isinstance(frequency, str):
                    self.frequency = Freq(frequency)
                elif isinstance(frequency, Freq):
                    self.frequency = frequency
                else:
                    raise ValueError("错误的Frequency类型")
        else:
            self.frequency = Freq.MIN1
        if start_time is not None:
            self.start_time = TimeTool.time_standardization(start_time)
        else:
            self.start_time = TimeTool.time_standardization('2008-01-01')
        if end_time is not None:
            self.end_time = TimeTool.time_standardization(end_time)
        else:
            self.end_time = TimeTool.get_now_time()

    def copy(self):
        return copy.deepcopy(self)


if __name__ == '__main__':
    # cod = Code('600001')
    # cod1 = cod.copy()
    # print(cod)
    # print(cod1)
    c = Code('AUL8')
    print(c.market)

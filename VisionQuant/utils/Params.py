from VisionQuant.utils import CfgTool

TDX_DIR = CfgTool.get_cfg('DataSource', 'tdx_dir')
LOCAL_DIR = CfgTool.get_cfg('DataSource', 'local_dir')
REMOTE_ADDR = CfgTool.get_cfg('DataSource', 'remote_addr')
DEFAULT_ASHARE_LOCAL_DATASOURCE = CfgTool.get_cfg('DataSource', 'ashare_local_source')
DEFAULT_ASHARE_LIVE_DATASOURCE = CfgTool.get_cfg('DataSource', 'ashare_live_source')
HDF5_COMPLIB = 'blosc:zstd'
HDF5_COMP_LEVEL = 5
DATASERVER_MAX_COUNT = int(CfgTool.get_cfg('DataServer', 'max_count'))

HQSERVER_HOST = CfgTool.get_cfg('HqServer', 'host')
HQSERVER_PORT = int(CfgTool.get_cfg('HqServer', 'port'))
RESPONSE_HEADER_LEN = 10
REQUEST_HEADER_LEN = 10
REQUEST_HEAD_KDATA = 0X01
REQUEST_HEAD_DATASERVER_SETTINGS = 0xaa
REQUEST_HEAD_BASIC_FINANCE_DATA = 0x10

LOG_DIR = CfgTool.get_cfg('Log', 'path')

"""
Market Type 市场类型
"""


class Market(object):
    class Ashare(object):
        class MarketSH(object):
            STOCK = 0
            KCB = 2
            INDEX = 4
            ETF = 6
            BOND = 8
            OTHERS = 10

        class MarketSZ(object):
            STOCK = 1
            CYB = 3
            INDEX = 5
            ETF = 7
            BOND = 9
            OTHERS = 10

    @staticmethod
    def is_ashare(market):
        if market in [Market.Ashare, Market.Ashare.MarketSH, Market.Ashare.MarketSZ, Market.Ashare.MarketSZ.STOCK,
                      Market.Ashare.MarketSZ.CYB, Market.Ashare.MarketSZ.ETF, Market.Ashare.MarketSZ.INDEX,
                      Market.Ashare.MarketSZ.BOND, Market.Ashare.MarketSH.STOCK, Market.Ashare.MarketSH.KCB,
                      Market.Ashare.MarketSH.ETF, Market.Ashare.MarketSH.INDEX, Market.Ashare.MarketSH.BOND]:
            return 1
        else:
            return 0


class Future(object):
    pass


class Crypto(object):
    pass


"""
K线周期
"""


class Freq(object):
    MIN1 = '1'
    MIN5 = '5'
    MIN15 = '15'
    MIN30 = '30'
    MIN60 = '60'
    MIN120 = '120'
    MIN240 = '240'
    DAY = 'd'
    WEEK = 'w'
    MONTH = 'm'


class OrderModel(object):
    """订单的成交模式
    LIMIT 限价模式
    MARKET 市价单 # 目前市价单在回测中是bar的开盘价 /实盘里面是五档剩余最优成交价
    CLOSE 收盘单 # 及在bar的收盘时的价格
    NEXT_OPEN 下一个bar的开盘价成交
    STRICT 严格订单 不推荐/仅限回测/是在当前bar的最高价买入/当前bar的最低价卖出
    @yutiansut/2017-12-18
    """
    LIMIT = 'LIMIT'  # 限价
    ANY = 'ANY'  # 市价(otg兼容)
    MARKET = 'MARKET'  # 市价/在回测里是下个bar的开盘价买入/实盘就是五档剩余最优成交价
    CLOSE = 'CLOSE'  # 当前bar的收盘价买入
    NEXT_OPEN = 'NEXT_OPEN'  # 下个bar的开盘价买入
    STRICT = 'STRICT'  # 严格模式/不推荐(仅限回测测试用)
    BEST = 'BEST'  # 中金所  最优成交剩余转限
    FIVELEVEL = 'FIVELEVEL'


class OrderLifeTime(object):
    IMMEDIATELY = 'IOC'  # 立即完成，否则撤销
    UNITLNEXTBAR = 'GNB'
    UNTILEND = 'GFD'  # 当日有效
    UNTILDATE = 'GTD'  # 指定日期前有效
    UNTILCANCEL = 'GTC'  # 撤销前有效
    GFA = 'GFA'  # 集合竞价有效


class OrderType(object):
    BUY = 'buy'
    CELL = 'cell'
    EMPTY = 'none'
    CANCEL_BUY = 'cb'
    CANCEL_SELL = 'cs'


class OrderStatus(object):
    NEW = 100
    SUCCESS_ALL = 200
    SUCCESS_PART = 203
    QUEUED = 300  # queued 用于表示在order_queue中 实际表达的意思是订单存活 待成交
    FAILED = 600


EXCEPT_CODELIST = ('888880', '516710', '516920', '516930', '510770', '512830', '513590', '516170', '516210', '516290',
                   '516560', '516630', '516640', '516790', '516860', '517030', '517800', '588390', '159715', '159875',
                   '159006')


def test_main(market):
    print(market)

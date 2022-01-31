from VisionQuant.Market.HqClient import HqClient
from VisionQuant.utils.Params import OrderLifeTime


class StrategyBase:
    def __init__(self, code, local_data=None, show_result=False):
        self.code = code
        self.data_struct = None
        self.hq_client = None
        self.show_result = show_result
        if local_data is not None:
            self.data_struct = local_data
        else:
            self.hq_client = HqClient()

    def get_data(self):
        if self.data_struct is not None:
            return self.data_struct
        else:
            return self.hq_client.get_kdata(self.code)

    def get_kdata(self, period='5'):
        return self.get_data().get_kdata(period)

    def get_basic_finance_data(self):
        res = self.hq_client.get_basic_finance_data(self.code)
        if res:
            return res
        else:
            return None

    def analyze(self):
        print(self.get_data().get_kdata('5').data_struct)

    def show(self, **kwargs):
        pass


class AnalyzeResult(object):
    def __init__(self, code: str, pp, efp, tp, sp, sp1):
        self.code = code
        self.present_price = pp
        self.exp_final_p = efp  # 预期成交价
        self.target_p = tp
        self.stop_p = sp
        self.stop_p1 = sp1

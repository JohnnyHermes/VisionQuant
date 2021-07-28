from VisionQuant.Market.HqClient import HqClient


class StrategyBase:
    def __init__(self, code):
        self.code = code
        self.hq_client = HqClient()

    def order(self):
        pass

    def get_data(self):
        return self.hq_client.get_data(self.code)

    def get_kdata(self, period='5'):
        return self.get_data().get_kdata(period)

    def analyze(self, ):
        print(self.get_data().get_kdata('5').data)

    def show(self):
        pass


class Order:
    def __init__(self):
        pass

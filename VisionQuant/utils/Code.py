from VisionQuant.utils import TimeTool
from VisionQuant.DataCenter import VQtdx


class Code:
    def __init__(self, code, frequency=None, start_time=None, end_time=None, fetch_data_method=None):
        self.code = code
        self.market = 'Ashare'  # todo:根据code自动判断市场类型
        if frequency is not None:
            self.frequency = frequency
        else:
            self.frequency = '5'
        if start_time is not None:
            self.start_time = TimeTool.time_standardization(start_time)
        else:
            self.start_time = TimeTool.time_standardization('2020-2-1')
        if end_time is not None:
            self.end_time = TimeTool.time_standardization(end_time)
        else:
            self.end_time = TimeTool.get_now_time()
        if fetch_data_method is not None:
            self.fetch_data_method = fetch_data_method
        else:
            self.fetch_data_method = VQtdx

    def __repr__(self):
        return self.code


if __name__ == '__main__':
    cod = Code('600001')
    print(cod)

from VisionQuant.DataStruct.Data import BaseDataStruct


class AShare(BaseDataStruct):
    def __init__(self, code, kdata_dict, finance_data=None):
        self.finance_data = finance_data
        super().__init__(code, kdata_dict)


if __name__ == '__main__':
    from VisionQuant.DataCenter import DataFetch, VQTdx
    from VisionQuant.utils.Code import Code
    import datetime

    code = Code(code='600639',
                frequency='5',
                start_time='2020-2-1',
                end_time='2021-06-25 15:00:00',
                fetch_data_method=VQTdx)
    test_data = DataFetch.fetch_kdata(code=code.code,
                                      frequency=code.frequency,
                                      method_func=code.fetch_data_method,
                                      start_time=code.start_time,
                                      end_time=code.end_time)

    test_data_dict = {'5': test_data}
    test = AShare(code.code, test_data_dict)
    print(test.get_kdata('5').filter('time', '2021-1-1 9:30', datetime.datetime(2021, 6, 24, 15, 0, 0),
                                     is_reset_index=False).data_struct)

    print(test.get_kdata('5').filter('time', '2021-1-1 9:30', datetime.datetime(2021, 6, 24, 15, 0, 0),
                                     is_reset_index=False).get_last_time())

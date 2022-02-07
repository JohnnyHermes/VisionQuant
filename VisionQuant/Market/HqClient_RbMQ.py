import pickle
from VisionQuant.Engine.RPCClient import RPCClient


class HqClient(RPCClient):

    def __init__(self, host='localhost'):
        super().__init__(host=host, routing_key='hqserver_rpc_queue')

    def get_kdata(self, codes):
        header = 'kdata'
        tmp_content = {'header': header, 'content': codes}
        content = pickle.dumps(tmp_content)
        response = self.call(content=content)
        return pickle.loads(response)

    def get_basic_finance_data(self, _code):
        header = 'basic_finance_data'
        tmp_content = {'header': header, 'content': _code}
        content = pickle.dumps(tmp_content)
        response = self.call(content=content)
        return pickle.loads(response)


if __name__ == '__main__':
    Hq_rpc = HqClient()
    from VisionQuant.utils.Code import Code

    print(" [x] Requesting data")
    code = Code('600639', '5')
    import time

    data = Hq_rpc.get_kdata(code)  # 约0.1s
    print(data.get_kdata('5').fliter(key='index', start=-10, end=-1).data)

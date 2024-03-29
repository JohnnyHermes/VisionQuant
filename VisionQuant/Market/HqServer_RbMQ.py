import pickle
from VisionQuant.Engine.RPCServer import RPCServer
from VisionQuant.DataCenter.DataServer import DataServer


class HqServer(RPCServer):
    def __init__(self, queue_name='hqserver_rpc_queue', force_live=False):
        self.data_server = DataServer(force_live=force_live)
        super().__init__(queue_name=queue_name)

    def process_request(self, body):
        request = pickle.loads(body)
        if request['header'] == 'kdata':
            data = self.data_server.get_data(request['content'])
            response = pickle.dumps(data)
            return response
        elif request['header'] == 'basic_finance_data':
            data = self.data_server.get_basic_finance_data(request['content'])
            response = pickle.dumps(data)
            return response


if __name__ == '__main__':
    server = HqServer()  # 普通版
    # server = HqServer(force_live=True)  # 强制连接到live服务器
    server.start()

import pickle
import struct
import socketserver

from VisionQuant.DataCenter.DataServer import DataServer
from VisionQuant.utils.Params import REQUEST_HEADER_LEN, REQUEST_HEAD_KDATA, REQUEST_HEAD_DATASERVER_SETTINGS, \
    REQUEST_HEAD_BASIC_FINANCE_DATA, HQSERVER_HOST, HQSERVER_PORT

data_server = DataServer()


class RequestHeaderRecvFailed(Exception):
    pass


class RequestBodyRecvFailed(Exception):
    pass


class HqServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            request_header_buf = self.request.recv(REQUEST_HEADER_LEN)
        except Exception as e:
            print(e)
            print(self.client_address, "连接断开")
        else:
            if len(request_header_buf) == REQUEST_HEADER_LEN:
                head, body_size, body_len = struct.unpack('>HII', request_header_buf)
                body_buf = bytearray()
                while True:
                    buf = self.request.recv(body_size)
                    len_buf = len(buf)
                    body_buf.extend(buf)
                    if not buf or len_buf == 0 or len(body_buf) == body_len:
                        break
                if not len(body_buf) == body_len:
                    raise RequestBodyRecvFailed("接收数据体失败服务器断开连接")
                if head == REQUEST_HEAD_KDATA:
                    code = pickle.loads(body_buf)
                    kdata = data_server.get_data(code)
                    response_body = pickle.dumps(kdata)
                    response_header = struct.pack('>HII', REQUEST_HEAD_KDATA, 102400, len(response_body))
                    self.request.sendall(response_header)
                    self.request.sendall(response_body)
                elif head == REQUEST_HEAD_BASIC_FINANCE_DATA:
                    code = pickle.loads(body_buf)
                    fian_data = data_server.get_basic_finance_data(code)
                    response_body = pickle.dumps(fian_data)
                    response_header = struct.pack('>HII', REQUEST_HEAD_BASIC_FINANCE_DATA, 10240, len(response_body))
                    self.request.sendall(response_header)
                    self.request.sendall(response_body)
                elif head == REQUEST_HEAD_DATASERVER_SETTINGS:
                    print("来自 {} 的dataserver配置修改请求:".format(self.client_address))
                    settings_dict = pickle.loads(body_buf)
                    data_server.configure(settings_dict)
                    response_body = bytes("修改DataServer配置成功！", encoding='utf-8')
                    self.request.sendall(response_body)
            else:
                raise RequestHeaderRecvFailed("head_buf is not 0x10 : " + str(request_header_buf))
        finally:
            self.request.close()

    def setup(self):
        pass

    def finish(self):
        pass


if __name__ == '__main__':
    with socketserver.ThreadingTCPServer((HQSERVER_HOST, HQSERVER_PORT), HqServerHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        print("行情服务器启动 host:{} port: {}".format(HQSERVER_HOST, HQSERVER_PORT))
        server.serve_forever()

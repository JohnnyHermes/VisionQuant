#! coding=utf-8
import socket
import pickle
import struct
from VisionQuant.utils.Params import RESPONSE_HEADER_LEN, REQUEST_HEAD_KDATA, REQUEST_HEAD_DATASERVER_SETTINGS, \
    REQUEST_HEAD_BASIC_FINANCE_DATA, HQSERVER_HOST, HQSERVER_PORT


class ResponseHeaderRecvFailed(Exception):
    pass


class ResponseBodyRecvFailed(Exception):
    pass


class HqClient:
    def __init__(self, addr=(HQSERVER_HOST, HQSERVER_PORT)):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_addr = addr

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.socket_addr)

    def close(self):
        self.socket.close()

    def get_kdata(self, codes):
        try:
            self.connect()
        except Exception as e:
            print(e)
            return None
        else:
            request_body = pickle.dumps(codes)
            request_flag = REQUEST_HEAD_KDATA
            request_header = struct.pack('>HII', request_flag, 1024, len(request_body))
            self.socket.sendall(request_header)
            self.socket.sendall(request_body)
            try:
                response_header_buf = self.socket.recv(RESPONSE_HEADER_LEN)
            except Exception as e:
                print(e)
                print(self.socket_addr, "接收response header失败")
            else:
                if len(response_header_buf) == RESPONSE_HEADER_LEN:
                    head, body_size, body_len = struct.unpack('>HII', response_header_buf)
                    if head == request_flag:
                        body_buf = bytearray()
                        while True:
                            buf = self.socket.recv(body_size)
                            len_buf = len(buf)
                            body_buf.extend(buf)
                            if not buf or len_buf == 0 or len(body_buf) == body_len:
                                break
                        if not len(body_buf) == body_len:
                            raise ResponseBodyRecvFailed("接收数据体失败服务器断开连接")
                        kdata_struct = pickle.loads(body_buf)
                        return kdata_struct
                    else:
                        raise ResponseHeaderRecvFailed("head is not {}, receive:{}".format(
                            request_flag, str(response_header_buf)))
                else:
                    raise ResponseHeaderRecvFailed("header_buf len is not {}, receive:{}".format(
                        RESPONSE_HEADER_LEN, str(response_header_buf)))
        finally:
            self.close()

    def configure_dataserver(self, **kwargs):
        try:
            self.connect()
        except Exception as e:
            print(e)
            return None
        else:
            request_body = pickle.dumps(kwargs)
            request_header = struct.pack('>HII', REQUEST_HEAD_DATASERVER_SETTINGS, 1024, len(request_body))
            self.socket.sendall(request_header)
            self.socket.sendall(request_body)
            try:
                response_buf = self.socket.recv(1024)
            except Exception as e:
                print(e)
                print(self.socket_addr, "接收response失败")
            else:
                print(bytes.decode(response_buf, encoding='utf-8'))
        finally:
            self.close()

    def get_basic_finance_data(self, _code):
        try:
            self.connect()
        except Exception as e:
            print(e)
            return None
        else:
            request_body = pickle.dumps(_code)
            request_flag = REQUEST_HEAD_BASIC_FINANCE_DATA
            request_header = struct.pack('>HII', request_flag, 1024, len(request_body))
            self.socket.sendall(request_header)
            self.socket.sendall(request_body)
            try:
                response_header_buf = self.socket.recv(RESPONSE_HEADER_LEN)
            except Exception as e:
                print(e)
                print(self.socket_addr, "接收response header失败")
            else:
                if len(response_header_buf) == RESPONSE_HEADER_LEN:
                    head, body_size, body_len = struct.unpack('>HII', response_header_buf)
                    if head == request_flag:
                        body_buf = bytearray()
                        while True:
                            buf = self.socket.recv(body_size)
                            len_buf = len(buf)
                            body_buf.extend(buf)
                            if not buf or len_buf == 0 or len(body_buf) == body_len:
                                break
                        if not len(body_buf) == body_len:
                            raise ResponseBodyRecvFailed("接收数据体失败服务器断开连接")
                        basic_data = pickle.loads(body_buf)
                        return basic_data
                    else:
                        raise ResponseHeaderRecvFailed("head is not {}, receive:{}".format(
                            request_flag, str(response_header_buf)))
                else:
                    raise ResponseHeaderRecvFailed("header_buf len is not {}, receive:{}".format(
                        RESPONSE_HEADER_LEN, str(response_header_buf)))
        finally:
            self.close()

    def __del__(self):
        self.socket.close()


if __name__ == '__main__':
    from VisionQuant.utils.Code import Code
    from VisionQuant.utils import TimeTool

    end_time = '2022-01-28 15:00:00'
    start_time = TimeTool.get_start_time(end_time, days=365 + 180)
    code = Code('002382', start_time=start_time, end_time=end_time)
    client = HqClient()
    data_struct = client.get_kdata(code)
    print(data_struct.get_kdata('5').data)
    print(client.get_basic_finance_data(code))
    # client.configure_dataserver(force_live=False, clean_data=1)

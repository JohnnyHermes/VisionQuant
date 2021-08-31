from VisionQuant.Market.HqClient import HqClient
import pika
import threading
import time


class StrategyThread(threading.Thread):
    def __init__(self, strategy):
        super().__init__()
        self.func = strategy.analyze
        self.lock = threading.Lock()
        self.result = None

    def run(self):
        with self.lock:
            self.result = self.func()

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            print(e)
            return None


class AnalyzeEngine:
    def __init__(self):
        self.code_pool = dict()

    def add_codes(self, codes_dict: dict):
        for key, codes_list in codes_dict.items():
            if key not in self.code_pool:
                self.code_pool[key] = codes_list
            else:
                for code in codes_list:
                    for exist_code in self.code_pool[key]:
                        if code.code == exist_code.code:  # for break else 若未中途跳出则执行else内语句
                            break
                    else:
                        self.code_pool[key].append(code)

    def register_strategy(self, strategy, codes, **kwargs):
        if 'show_result' in kwargs:
            show_result = kwargs['show_result']
        else:
            show_result = False
        if not isinstance(codes, list):
            if 'local_data' in kwargs:
                strategy_obj = strategy(codes, kwargs['local_data'], show_result)
            else:
                strategy_obj = strategy(codes, show_result=show_result)
            self.code_pool[codes.code] = strategy_obj
        else:
            for code in codes:
                if 'local_data' in kwargs:
                    strategy_obj = strategy(code, kwargs['local_data'][code.code], show_result)
                else:
                    strategy_obj = strategy(code, show_result=show_result)
                self.code_pool[code.code] = strategy_obj

    def run_strategy(self, codes):
        if not isinstance(codes, list):
            thread = StrategyThread(strategy=self.code_pool[codes.code])
            thread.start()
            thread.join()
            return thread.get_result()
        else:
            result_dict = dict()
            for code in codes:
                thread = StrategyThread(strategy=self.code_pool[code.code])
                thread.start()
                thread.join()
                result_dict[code.code] = thread.get_result()
            return result_dict

# class AnalyzeEngine:
#     def __init__(self, hq_host='localhost'):
#         self.hq_client = HqClient(host=hq_host)
#         self._queue_dict = dict()
#         connection = pika.BlockingConnection(
#             pika.ConnectionParameters(host='localhost'))
#         self.channel = connection.channel()
#         self.exchange = self.channel.exchange_declare(exchange='analyze_data', exchange_type='direct')
#
#     def register(self, code, strategy):
#         new_queue = self.channel.queue_declare(queue='', exclusive=True)
#         queue_name = new_queue.method.queue
#         self._queue_dict[code.code] = (queue_name, strategy, 0)
#         self.channel.queue_bind(exchange='analyze_data', queue=queue_name, routing_key=queue_name)
#
#     def start_strategy(self, codes):
#         if not isinstance(codes, list):
#             codes = list(codes)
#         for code in codes:
#             try:
#                 queue_name, strategy, _ = self._query_queue(code)
#                 self.channel.basic_consume(queue=queue_name, on_message_callback=strategy.callback, auto_ack=True)
#                 self._queue_dict[code.code] = (queue_name, strategy, 1)
#             except ValueError as e:
#                 print(e)
#                 continue
#
#     def stop_strategy(self, codes):
#         pass
#
#     def query_strategy_status(self, code):
#         return self._query_queue(code)[2]
#
#     def _query_queue(self, code):
#         if code.code in self._queue_dict:
#             return self._queue_dict[code.code]
#         else:
#             raise ValueError("未注册该品种")
#
#     def _publish_data(self, data):
#         request_id = data[0]
#         response_body = data[1]
#         self.channel.basic_publish(exchange='analyze_data', routing_key=request_id, body=response_body)
#
#     def update(self):
#         for content in self._queue_dict.values():
#             if content[2]:
#                 response = self.hq_client.get_data(codes=content[1].code, request_id=content[0])
#                 print(1)
#                 self._publish_data(response)
#                 print(response)
#             else:
#                 continue

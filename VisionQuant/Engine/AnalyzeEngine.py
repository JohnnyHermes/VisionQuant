from VisionQuant.Market.HqClient import HqClient
import pika
import threading
import time


class StrategyThread:
    def __init__(self, code, strategy):
        self.code = code
        self.strategy = strategy

    def start(self):
        thread = threading.Thread(target=self.strategy.analyze)
        thread.start()


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

    def register_strategy(self, strategy, codes):
        if not isinstance(codes, list):
            strategy_obj = strategy(codes)
            self.code_pool[codes.code] = StrategyThread(code=codes, strategy=strategy_obj)
        else:
            for code in codes:
                strategy_obj = strategy(code)
                self.code_pool[code.code] = StrategyThread(code=code, strategy=strategy_obj)
                print(code.code)

    def run_strategy(self, codes):
        if not isinstance(codes, list):
            self.code_pool[codes.code].start()
        else:
            for code in codes:
                self.code_pool[code.code].start()


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

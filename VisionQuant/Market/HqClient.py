import pickle

import pika
import uuid


class HqClient():

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.response = None
        self.corr_id = None
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def get_data(self, codes):
        content = pickle.dumps(codes)
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=content)
        while self.response is None:
            self.connection.process_data_events()
        return pickle.loads(self.response)


if __name__ == '__main__':
    Hq_rpc = HqClient()
    from VisionQuant.utils.Code import Code

    print(" [x] Requesting data")
    code = Code('600639', '5')
    import time
    response = Hq_rpc.get_data(code)  # 约0.1s
    print(response.get_kdata('5').data)

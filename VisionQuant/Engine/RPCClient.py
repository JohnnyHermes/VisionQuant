import pika
import uuid


class RPCClient:

    def __init__(self, host='localhost', routing_key='rpc_queue'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.response = None
        self.corr_id = None
        self.routing_key = routing_key
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

    def call(self, content):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=content)
        while self.response is None:
            self.connection.process_data_events()
        # print('received response')
        return self.response

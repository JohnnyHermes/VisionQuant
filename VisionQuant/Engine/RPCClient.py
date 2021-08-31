import pika
import uuid
from pika.exceptions import StreamLostError, ChannelWrongStateError


class RPCClient:

    def __init__(self, host='localhost', routing_key='rpc_queue'):
        self.response = None
        self.corr_id = None
        self.routing_key = routing_key
        self.host = host
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.connect()

    def connect(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
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
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.routing_key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                ),
                body=content)
        except (StreamLostError, ChannelWrongStateError):
            self.connect()
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

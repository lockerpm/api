import pika
import json

from django.conf import settings

from shared.services.rabbitmq.exceptions import *


class MessageBroker(object):
    def send(self, *args, **kwargs):
        raise NotImplementedError


class RabbitMQ(MessageBroker):
    def __init__(self):
        self.connection = None
        self.queue_name = None

    @staticmethod
    def connect(url_connection, timeout: int = 5):
        parameters = pika.URLParameters(url_connection)
        parameters.socket_timeout = timeout
        try:
            connection = pika.BlockingConnection(parameters)
        except:
            raise RabbitConnectionError
        return connection

    def send(self, data):
        if self.queue_name is None:
            print("VLC None")
            raise QueueNotSetError
        if self.connection is None:
            raise RabbitConnectionError
        try:
            channel = self.connection.channel()
            channel.queue_declare(queue=self.queue_name, durable=True)
            channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=data,
                properties=pika.BasicProperties(
                    delivery_mode=2         # make message persistent
                )
            )
        except:
            raise RabbitMQSendError
        finally:
            self.close()

    def close(self):
        if self.connection:
            self.connection.close()


class RelayQueue(RabbitMQ):
    def __init__(self):
        super(RelayQueue, self).__init__()
        self.connection = self.connect(url_connection=settings.RELAY_QUEUE_URL)
        self.queue_name = settings.RELAY_QUEUE

    def send(self, data):
        data = json.dumps(data)
        super(RelayQueue, self).send(data)

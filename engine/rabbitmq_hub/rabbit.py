import amqp
import json
import socket
import sys, os


class CallbackWrapper(object):
    def __init__(self, topic, callback):
        self.topic = topic
        self._callback = callback

    def __str__(self):
        return ('CallbackWrapper<topic: %s, callback: %s>'
                % (self.topic, self.callback.__name__))

    def callback(self, msg):
        if self._callback is not None:
            if msg.content_type == 'application/json':
                try:
                    message = json.loads(msg.body)
                except Exception:
                    message = msg.body
            else:
                message = msg.body
            self._callback(self.topic, message)


class RabbitConnection(object):
    """
    Manage connections to rabbitmq-server
    """
    description_format = 'RabbitConnection<host=(%(host)s, %(port)s),virtual_host=%(virtual_host)s>'

    def __init__(self, host="127.0.0.1", port=5672, user='guest', password='guest',
                 virtual_host='/', **kwargs):
        self.pid = os.getpid()
        self.host = host
        self.port = port
        self.user, self.password = user, password
        self.virtual_host = virtual_host
        self.connkwargs = {
                'host': self.host,
                'userid': self.user,
                'password': self.password,
                'virtual_host': self.virtual_host,
                }
        self.connkwargs.update(kwargs)
        self._connection = None
        self._channel = None
        self._exchanges = set()
        self._description_args = {
            'host': self.host,
            'port': self.port,
            'virtual_host': self.virtual_host
        }
        self._handlers = {}

    def __str__(self):
        return self.description_format % self._description_args

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def _register_handlers(self):
        for h in self._handlers.values():
            self.subscribe(h['topic'], h['queue_group'], h['callback'])

    @property
    def connection(self):
        if self._connection is None or not self._connection.connected:
            self.connect()
        return self._connection

    @property
    def channel(self):
        if self._connection is None or not self._connection.connected:
            self.connect()
        return self._channel

    def publish(self, msg, exchange_name, routing_key, mandatory=False, immediate=False):
        if exchange_name not in self._exchanges:
            self.channel.exchange_declare(exchange_name, 'topic', durable=True, auto_delete=False)
            self._exchanges.add(exchange_name)
        self.channel.basic_publish(msg, exchange_name, routing_key, mandatory, immediate)

    def subscribe(self, topic, queue_group, callback=None):
        if '*' in topic or '#' in topic:
            print('* and # wildcard will not support in the next rabbitmq_hub. Use the topic fullname directly.')

        self._handlers[topic] = dict(topic=topic, queue_group=queue_group, callback=callback)

        exchange_name = topic.split('.', 1)[0]
        queue_name = '%s.%s' % (topic, queue_group)

        self.channel.exchange_declare(exchange_name, 'topic', durable=True, auto_delete=False)
        self.channel.queue_declare(queue_name, durable=True)
        self.channel.queue_bind(queue_name, exchange_name, topic)

        wrapper = CallbackWrapper(topic, callback)
        self.channel.basic_consume(queue_name, callback=wrapper.callback, no_ack=True)

    def readloop(self):
        try:
            self.connection.drain_events()
        except IOError:
            raise ConnectionError('readloop connetion error.')

    def connect(self):
        if self._connection:
            return
        try:
            self._connection = amqp.Connection(**self.connkwargs)
            self._connection.connect()
            self._channel = self._connection.channel()
            self._register_handlers()
        except Exception:
            raise ConnectionError('Connect failed')

    def disconnect(self):
        if self._connection is None:
            return
        try:
            self._connection.close()
        except socket.error:
            pass
        except IOError:
            pass
        self._connection = None
        self._channel = None
        self._exchanges.clear()

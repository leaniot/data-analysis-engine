import amqp
import json
import socket
from functools import partial
import time


class Handler(object):
    def __init__(self, exchange_name, queue_name, binding_key, callback):
        self.exchange_name = exchange_name
        self.queue_name = queue_name
        self.binding_key = binding_key
        self._callback = callback

    def __str__(self):
        return ('handler<exchange: %s, queue: %s, binding_key: %s, callback: %s>'
                % (self.exchange_name, self.queue_name, self.binding_key,
                    self.callback.__name__))

    def callback(self, msg):
        if self._callback is not None:
            if msg.content_type == 'application/json':
                try:
                    message = json.loads(msg.body)
                except Exception:
                    message = msg.body
            else:
                message = msg.body
            self._callback(self.binding_key, message)


class Sub(object):
    """
    Manage connections to the broker for the consumer.

    :type name: str
    :param name: the name of the subscriber. If multiple subscribers with the same name
                 subscribe the same topic, messages will be delivered to these subscribers
                 in a round-robin way.

    :type host: str
    :param host: the host to connect to, which should be 'host[:port]', if
                 no port is specified then 5672 is used.
    """
    def __init__(self, name, host='localhost', user='guest', password='guest',
                 virtual_host='/', connect_timeout=None, reconnect_interval=30, **kwargs):
        self.connkwargs = {
                'host': host,
                'userid': user,
                'password': password,
                'virtual_host': virtual_host,
                'connect_timeout': connect_timeout,
                }
        self.reconnect_interval = reconnect_interval
        self._name = name
        self._connection = None
        self._channel = None
        self._handlers = {}

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def _connect(self):
        if self._connection is not None:
            return
        try:
            self._connection = amqp.Connection(**self.connkwargs)
            self._connection.connect()
            self._channel = self._connection.channel()
        except Exception:
            raise ConnectionError('Connect failed')

        self._register_handlers()

    def _register_handlers(self):
        for h in self._handlers.values():
            self._channel.exchange_declare(h.exchange_name, 'topic', durable=True, auto_delete=False)
            self._channel.queue_declare(h.queue_name, durable=True)
            self._channel.queue_bind(h.queue_name, h.exchange_name, h.binding_key)
            self._channel.basic_consume(h.queue_name, callback=partial(h.callback), no_ack=True)

    @property
    def connection(self):
        if not self._connection:
            try:
                self._connect()
            except:
                pass
        return self._connection

    def disconnect(self):
        if self._connection is None:
            return
        try:
            self._connection.close()
        except socket.error:
            pass
        self._connection = None
        self._channel = None

    def shutdown(self):
        try:
            if self._connection and self._connection.transport:
                self._connection.transport.close()
        except socket.error:
            pass
        self._connection = None
        self._channel = None

    def subscribe(self, topic, callback=None):
        """
        Subscribe messages on a specified topic with a specified message handler.

        :type topic: str
        :param topic: the specified topic to subscribe, should be in 'a.b.c' format.
        :type callback: callable object
        :param callback: the messsage handler: callback(topic, message)

                      * topic: the topic you have subscribed to
                      * message: the message deliverd to the topic, str or dict

        """
        if '*' in topic or '#' in topic:
            print('* and # wildcard will not support in the next rabbitmq_hub. Use the topic fullname directly.')
        exchange_name = topic.split('.')[0]
        queue_name = '%s.%s' % (topic, self._name)
        binding_key = topic

        def decorator(callback):
            handler = Handler(exchange_name, queue_name, binding_key, callback)
            self._handlers[topic] = handler
            return callback
        return decorator(callback) if callback else decorator

    def drain_events(self):
        """
        Get a message from the topic you have subscribed and call the callback, it will not return util the callback
        returns
        """
        connection = self.connection
        if connection:
            try:
                connection.drain_events()
            except IOError:
                self.shutdown()
            except:
                self.disconnect()
                raise
        else:
            time.sleep(self.reconnect_interval)

    def run(self):
        """
        Run a infinite loop to handle messages from the topic you have subscribed continously.
        """
        while True:
            self.drain_events()

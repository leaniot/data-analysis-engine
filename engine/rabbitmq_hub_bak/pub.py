
import amqp
import json
import socket
from itertools import chain


class Pub(object):
    """
    Manage connections to the broker for the producer.

    :type host: str
    :param host: the host to connect to, which should be 'host[:port]', if
                 no port is specified then 5672 is used.
    """
    def __init__(self, host='localhost', user='guest', password='guest',
                 virtual_host='/', connect_timeout=3, **kwargs):
        connkwargs = {
                'host': host,
                'userid': user,
                'password': password,
                'virtual_host': virtual_host,
                'connect_timeout': connect_timeout,
                }
        self._pool = ConnectionPool(**connkwargs)

    def __del__(self):
        self._pool.disconnect()

    def publish(self, msg, topic, delivery_mode=1, **properties):
        """
        Publish a msg with a specified topic.

        :type msg: str or dict
        :param msg: the message to publish.

        :type topic: str
        :param topic: the specified topic, should be in 'a.b.c' format,
                      for example, 'instalikes.user.login'.
        """
        exchange_name = topic.split('.')[0]
        routing_key = topic

        content_type = 'text/plain'
        if isinstance(msg, dict):
            msg = json.dumps(msg)
            content_type = 'application/json'
        message = amqp.Message(msg, content_type=content_type, delivery_mode=delivery_mode,  **properties)
        pool = self._pool
        connection = pool.get_connection()
        try:
            return connection.publish(message, exchange_name, routing_key)
        except socket.error:
            connection.shutdown()
            try:
                return connection.publish(message, exchange_name, routing_key)
            except socket.error:
                connection.shutdown()
            except ConnectionError:
                pass
            except Exception:
                connection.disconnect()
        except ConnectionError:
            pass
        except Exception:
            connection.disconnect()
        finally:
            pool.release(connection)


class Connection(object):
    "Manage connections to rabbitmq-server"
    description_format = 'Connection<host=%(host)s,virtual_host=%(virtual_host)s>'

    def __init__(self, **kwargs):
        self.connkwargs = kwargs
        self._connection = None
        self._channel = None
        self._exchanges = set()

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def publish(self, msg, exchange_name, routing_key, mandatory=False, immediate=False):
        if self._connection is None or not self._connection.connected:
            self.connect()
        if exchange_name not in self._exchanges:
            self._channel.exchange_declare(exchange_name, 'topic', durable=True, auto_delete=False)
            self._exchanges.add(exchange_name)
        self._channel.basic_publish(msg, exchange_name, routing_key, mandatory, immediate)

    def connect(self):
        try:
            self._connection = amqp.Connection(**self.connkwargs)
            self._connection.connect()
            self._channel = self._connection.channel()
        except Exception:
            raise ConnectionError('Connect failed')

    def disconnect(self):
        if self._connection is None:
            return
        try:
            self._connection.close()
        except socket.error:
            pass
        self._connection = None
        self._channel = None
        self._exchanges.clear()

    def shutdown(self):
        try:
            if self._connection and self._connection.transport:
                self._connection.transport.close()
        except socket.error:
            pass
        self._connection = None
        self._channel = None
        self._exchanges.clear()


class ConnectionPool(object):
    def __init__(self, connection_class=Connection, max_connections=None, **kwargs):
        self.connection_class = connection_class
        self.max_connections = max_connections or 2 ** 31
        self.connkwargs = kwargs
        self._created_connections = 0
        self._available_connections = []
        self._in_use_connections = set()

    def __str__(self):
        return self.connection_class % self.connkwargs

    def make_connection(self):
        if self._created_connections >= self.max_connections:
            raise ConnectionError('Too many connections')
        self._created_connections += 1
        return self.connection_class(**self.connkwargs)

    def get_connection(self):
        try:
            connection = self._available_connections.pop()
        except IndexError:
            connection = self.make_connection()
        self._in_use_connections.add(connection)
        return connection

    def release(self, connection):
        self._in_use_connections.remove(connection)
        self._available_connections.append(connection)

    def disconnect(self):
        all_conns = chain(self._available_connections,
                          self._in_use_connections)
        for connection in all_conns:
            connection.disconnect()


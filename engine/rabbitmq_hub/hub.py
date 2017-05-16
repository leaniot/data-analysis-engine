import json
import socket
import logging
import amqp
from .connection import ConnectionCluster, wait_func
from .rabbit import RabbitConnection
try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse

logger = logging.getLogger(__file__)


class PubSubHub(object):
    def __init__(self, connection_class=RabbitConnection, queue_group=None, **kwargs):
        self.pub_conncluster = ConnectionCluster(connection_class=connection_class, max_connections=100, **kwargs)
        self.sub_conncluster = ConnectionCluster(connection_class=connection_class, max_connections=1, **kwargs)
        self.queue_group = queue_group or 'none'

    def __del__(self):
        self.pub_conncluster.disconnect()
        self.sub_conncluster.disconnect()

    @classmethod
    def create(cls, server_urls, **kwargs):
        if not isinstance(server_urls, (list, tuple)):
            server_urls = [server_urls]

        endpoints = []
        for url in server_urls:
            args = {}
            parsed = urlparse.urlparse(url)
            virtual_host = parsed.path.strip('/') or '/'
            args.update(host=parsed.hostname, port=parsed.port, virtual_host=virtual_host)
            if parsed.username:
                args.update(user=parsed.username)
            if parsed.password:
                args.update(password=parsed.password)
            if parsed.query:
                query_args = urlparse.parse_qs(parsed.query)
                query_args = dict(map(lambda x: (x[0], x[1][0]), query_args.items()))
                args.update(query_args)
            if 'socket_connect_timeout' not in args:
                args.update(socket_connect_timeout=3)
            endpoints.append(args)
        kwargs.update(endpoints=endpoints)
        return cls(**kwargs)

    def publish(self, msg, topic, **kwargs):
        exchange_name = topic.split('.')[0]
        routing_key = topic
        content_type = 'text/plain'
        if isinstance(msg, (list, dict)):
            msg = json.dumps(msg)
            content_type = 'application/json'
        message = amqp.Message(msg, content_type=content_type, delivery_mode=1,  **kwargs)
        num = len(self.pub_conncluster.all_connection_pools())
        for i in range(num):
            try:
                connection = self.pub_conncluster.get_connection()
                if not connection:
                    continue
            except Exception as e:
                logger.error(e)
                continue
            try:
                return connection.publish(message, exchange_name, routing_key)
            except socket.error as e:
                logger.error(e)
                self.pub_conncluster.connection_error(connection)
            except ConnectionError as e:
                logger.error(e)
                self.pub_conncluster.connection_error(connection)
            except Exception as e:
                logger.error(e)
                connection.disconnect()
            finally:
                self.pub_conncluster.release(connection)
        logger.error('PUB FAIL', {'topic': topic, 'msg': msg})

    def subscribe(self, topic, callback=None):
        def decorator(callback_fn):
            for pool in self.sub_conncluster.all_connection_pools():
                connection = pool.get_connection()
                try:
                    connection.subscribe(topic, self.queue_group, callback=callback_fn)
                except:
                    logger.info('subscribe failed to connection<%s> with topic<%s> and queue_group<%s>'%(connection, topic, self.queue_group))
                finally:
                    pool.release(connection)
            return callback_fn
        return decorator(callback) if callback else decorator

    def run(self):
        self.sub_conncluster.start_readloop()

    def join(self, timeout=3):
        wait_func()
        self.sub_conncluster.join(timeout)

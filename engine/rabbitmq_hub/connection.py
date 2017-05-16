import json
import socket
import sys
import os
import ssl
import random
import errno
from six import string_types
from itertools import chain
# Change queue (Py 3.*) to Queue (Py 2.7.*)
from Queue import LifoQueue, Empty, Full

# if socket.socket.__module__ == "gevent.socket":
if socket.socket.__module__ == "gevent._socket3":
    import gevent
    import gevent.threading
    spawn_func = gevent.spawn
    sleep_func = gevent.sleep
    kill_func = gevent.kill
    lock_class = gevent.threading.Lock
    wait_func = gevent.wait
else:
    import time
    import threading

    def threading_spawn(func, *args, **kwargs):
        t = threading.Thread(target=func, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
        return t

    def threading_wait():
        while 1:
            try:
                time.sleep(3)
            except (KeyboardInterrupt, SystemExit):
                sys.exit()
    spawn_func = threading_spawn
    sleep_func = time.sleep
    lock_class = threading.Lock
    wait_func = threading_wait


class Connection(object):
    """
    Manages TCP communication to and from a server
    """
    description_format = "Connection<host:%(host)s,port:%(port)s,id:%(id)s>"

    def __init__(self, host, port, socket_connect_timeout=None, socket_timeout=None, **kwargs):
        self.pid = os.getpid()
        self.host = host
        self.port = int(port)
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout or socket_timeout
        self._sock = None
        self._description_args = {
            'host': self.host,
            'port': self.port,
            'id': id(self)
        }
        self._connect_callbacks = []
        self.buffer = ''
        self.ssl_conn = False
        if 'ssl_keyfile' in kwargs or 'ssl_certfile' in kwargs:
            self.ssl_conn = True
            self.keyfile = kwargs['ssl_keyfile']
            self.certfile = kwargs['ssl_certfile']
            ssl_cert_reqs = kwargs.get('ssl_cert_reqs') or ssl.CERT_NONE
            ssl_ca_certs = kwargs.get('ssl_ca_certs')
            if isinstance(ssl_cert_reqs, string_types):
                cert_reqs = {
                    'none': ssl.CERT_NONE,
                    'optional': ssl.CERT_OPTIONAL,
                    'required': ssl.CERT_REQUIRED
                }
                if ssl_cert_reqs not in cert_reqs:
                    raise Exception("Invalid SSL Certificate Requirements Flag: %s" % ssl_cert_reqs)
                ssl_cert_reqs = cert_reqs[ssl_cert_reqs]
            self.cert_reqs = ssl_cert_reqs
            self.ca_certs = ssl_ca_certs

    def __repr__(self):
        return self.description_format % self._description_args

    def __del__(self):
        try:
            self.disconnect()
        except Exception:
            pass

    def register_connect_callback(self, callback):
        self._connect_callbacks.append(callback)

    def clear_connect_callbacks(self):
        self._connect_callbacks = []

    def connect(self):
        """
        Connects to the server if not already connected
        """
        if self._sock:
            return
        try:
            sock = self._connect()
        except socket.error:
            e = sys.exc_info()[1]
            raise ConnectionError(self._error_message(e))

        self._sock = sock
        try:
            self.on_connect()
        except:
            # clean up after any error in on_connect
            self.disconnect()
            raise

        # run any user callbacks. right now the only internal callback
        # is for rabbitmq_hub channel/pattern resubscription
        for callback in self._connect_callbacks:
            callback(self)

    def _connect(self):
        """
        Create a TCP socket connection
        """
        # we want to mimic what socket.create_connection does to support
        # ipv4/ipv6, but we want to set options prior to calling
        # socket.connect()
        resources = socket.getaddrinfo(self.host, self.port, socket.AF_INET, socket.SOCK_STREAM)
        if len(resources) == 0:
            raise Exception("getaddrinfo returns an empty list")

        index = random.randint(1, len(resources))
        start = index % len(resources)

        for i in range(len(resources)):
            family, socktype, proto, canonname, socket_address = resources[(start+i) % len(resources)]
            sock = None

            try:
                sock = socket.socket(family, socktype, proto)
                # TCP_NODELAY
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                # set the socket_connect_timeout before we connect
                sock.settimeout(self.socket_connect_timeout)

                # connect
                sock.connect(socket_address)

                # set the socket_timeout now that we're connected
                sock.settimeout(self.socket_timeout)

                if self.ssl_conn:
                    sock = ssl.wrap_socket(sock, cert_reqs=self.cert_reqs, keyfile=self.keyfile,
                                           certfile=self.certfile, ca_certs=self.ca_certs)
                return sock

            except socket.error as _:
                err = _
                if sock is not None:
                    sock.close()
                if i == len(resources)-1:
                    raise

        raise socket.error("socket.getaddrinfo returned an empty list")

    def _error_message(self, exception):
        # args for socket.error can either be (errno, "message")
        # or just "message"
        if len(exception.args) == 1:
            return "Error connecting to %s:%s. %s." % \
                (self.host, self.port, exception.args[0])
        else:
            return "Error %s connecting to %s:%s. %s." % \
                (exception.args[0], self.host, self.port, exception.args[1])

    def on_connect(self):
        pass

    def disconnect(self):
        """
        Disconnects from the server
        :return: 
        """
        if self._sock is None:
            return
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
        except socket.error:
            pass
        self._sock = None
        self.on_disconnect()

    def on_disconnect(self):
        pass

    def connection(self):
        if not self._sock:
            self.connect()
        return self._sock

    def _read(self, n=None):
        sock = self.connection()
        return sock.recv(n)

    def read(self, bytes):
        while len(self.buffer) < bytes:
            data = None
            try:
                data = self._read(1024)
            except socket.error as ex:
                if ex.args[0] == errno.EINTR:
                    continue
                raise ex
            if not data:
                break
            self.buffer += data
        result = self.buffer[:bytes]
        self.buffer = self.buffer[bytes:]
        return str(result)

    def write(self, string):
        sock = self.connection()
        try:
            return sock.sendall(string)
        except:
            self.disconnect()
            raise


class ConnectionPool(object):
    def __init__(self, connection_class=Connection, max_connections=None, **kwargs):
        self.connection_class = connection_class
        self.max_connections = max_connections or 2 ** 31
        self.connection_kwargs = kwargs

        self.reset()

    def __repr__(self):
        return "%s<%s>" % (
            type(self).__name__,
            self.connection_class.description_format % self.connection_kwargs,
        )

    def reset(self):
        self.pid = os.getpid()
        self._created_connections = 0
        self._available_connections = []
        self._in_use_connections = set()
        self._check_lock = lock_class()

    def _checkpid(self):
        if self.pid != os.getpid():
            with self._check_lock:
                if self.pid == os.getpid():
                    # another thread already did the work while we waited
                    # on the lock.
                    return
                self.disconnect()
                self.reset()

    def get_connection(self):
        "Get a connection from the pool"
        self._checkpid()
        try:
            connection = self._available_connections.pop()
        except IndexError:
            connection = self.make_connection()
        self._in_use_connections.add(connection)
        return connection

    def make_connection(self):
        "Create a new connection"
        if self._created_connections >= self.max_connections:
            raise ConnectionError("Too many connections")
        self._created_connections += 1
        return self.connection_class(**self.connection_kwargs)

    def release(self, connection):
        "Releases the connection back to the pool"
        self._checkpid()
        if connection.pid != self.pid:
            return
        self._in_use_connections.remove(connection)
        self._available_connections.append(connection)

    def disconnect(self):
        "Disconnects all connections in the pool"
        all_conns = chain(self._available_connections,
                          self._in_use_connections)
        for connection in all_conns:
            connection.disconnect()


class BlockingConnectionPool(ConnectionPool):
    """
    Thread-safe blocking connection pool.
    It performs the same function as the default
    ``:py:class: ~dock.common.connection.ConnectionPool`` implementation, in that,
    it maintains a pool of reusable connections (safely across threads if required).
    The difference is that, in the event that a client tries to get a
    connection from the pool when all of connections are in use, rather than
    raising a ``:py:class: ~dock.common.exceptions.ConnectionError`` (as the default
    ``:py:class: ~dock.common.connection.ConnectionPool`` implementation does), it
    makes the client wait ("blocks") for a specified number of seconds until
    a connection becomes available.
    Use ``max_connections`` to increase / decrease the pool size::
        >>> pool = BlockingConnectionPool(max_connections=10)
    Use ``timeout`` to tell it either how many seconds to wait for a connection
    to become available, or to block forever:
        # Block forever.
        >>> pool = BlockingConnectionPool(timeout=None)
        # Raise a ``ConnectionError`` after five seconds if a connection is
        # not available.
        >>> pool = BlockingConnectionPool(timeout=5)
    """
    def __init__(self, max_connections=100, timeout=6,
                 connection_class=Connection, queue_class=LifoQueue,
                 **connection_kwargs):

        self.queue_class = queue_class
        self.timeout = timeout
        super(BlockingConnectionPool, self).__init__(
            connection_class=connection_class,
            max_connections=max_connections,
            **connection_kwargs)

    def reset(self):
        self.pid = os.getpid()
        self._check_lock = lock_class()

        # Create and fill up a thread safe queue with ``None`` values.
        self.pool = self.queue_class(self.max_connections)
        while True:
            try:
                self.pool.put_nowait(None)
            except Full:
                break

        # Keep a list of actual connection instances so that we can
        # disconnect them later.
        self._connections = []

    def make_connection(self):
        "Make a fresh connection."
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self):
        """
        Get a connection, blocking for ``self.timeout`` until a connection
        is available from the pool.
        If the connection returned is ``None`` then creates a new connection.
        Because we use a last-in first-out queue, the existing connections
        (having been returned to the pool after the initial ``None`` values
        were added) will be returned before ``None`` values. This means we only
        create new connections when we need to, i.e.: the actual number of
        connections will only increase in response to demand.
        """
        # Make sure we haven't changed process.
        self._checkpid()

        # Try and get a connection from the pool. If one isn't available within
        # self.timeout then raise a ``ConnectionError``.
        # connection = None
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            raise ConnectionError("No connection available.")

        # If the ``connection`` is actually ``None`` then that's a cue to make
        # a new connection to add to the pool.
        if connection is None:
            connection = self.make_connection()

        return connection

    def release(self, connection):
        "Releases the connection back to the pool."
        # Make sure we haven't changed process.
        self._checkpid()
        if connection.pid != self.pid:
            return

        # Put the connection back into the pool.
        try:
            self.pool.put_nowait(connection)
        except Full:
            # perhaps the pool has been reset() after a fork? regardless,
            # we don't want this connection
            pass

    def disconnect(self):
        "Disconnects all connections in the pool."
        for connection in self._connections:
            connection.disconnect()


class ConnectionCluster(object):
    CHECK_INTERVAL = 10

    def __init__(self, connection_class=Connection, connection_pool_class=ConnectionPool, endpoints=[], **kwargs):
        self.connection_class = connection_class
        self.connection_pool_class = connection_pool_class

        self.endpoints = dict(map(lambda x: ('%s:%s' % (x['host'], x['port']), x), endpoints))

        for k, v in self.endpoints.items():
            v['connection_class'] = self.connection_class
            v.update(kwargs)

        self._available_pools = {}
        self._checking_pools = set()
        for k, v in self.endpoints.items():
            self._available_pools[k] = self.connection_pool_class(**v)
        self._processors = []

    def all_connection_pools(self):
        return list(self._available_pools.values())

    def get_connection(self):
        if not self._available_pools:
            return None
        index = random.randint(1, len(self._available_pools)) % len(self._available_pools)
        pool = self.all_connection_pools()[index]
        conn = pool.get_connection()
        try:
            conn.connect()
        except socket.error:
            self.connection_error(conn)
        except ConnectionError:
            self.connection_error(conn)
        return conn

    def release(self, connection):
        key = '%s:%s'%(connection.host, connection.port)
        pool = self._available_pools.get(key)
        if pool:
            pool.release(connection)

    def disconnect(self):
        for k, pool in self._available_pools.items():
            try:
                pool.disconnect()
            except:
                pass

    def join(self, timeout=3):
        for thread in self._processors:
            try:
                thread.join(timeout)
            except (KeyboardInterrupt, SystemExit):
                print('Shutting down ...')

    def connection_error(self, connection):
        connection.disconnect()
        self.release(connection)
        key = '%s:%s'%(connection.host, connection.port)
        if key not in self._checking_pools:
            pool = self._available_pools.pop(key)
            spawn_func(self.check_endpoint, key, pool)
            self._checking_pools.add(key)

    def check_endpoint(self, key, pool):
        while 1:
            conn = pool.get_connection()
            try:
                conn.connect()
                self._available_pools[key] = pool
                self._checking_pools.remove(key)
                break
            except socket.error:
                sleep_func(self.CHECK_INTERVAL)
            except ConnectionError:
                sleep_func(self.CHECK_INTERVAL)
            except:
                sleep_func(self.CHECK_INTERVAL)
            finally:
                pool.release(conn)

    def start_readloop(self):
        funcs = []
        for pool in self._available_pools.values():
            funcs.append(spawn_func(self._conn_readloop, pool))
        self._processors = funcs
        return funcs

    def _conn_readloop(self, pool):
        while 1:
            try:
                connection = pool.get_connection()
            except:
                sleep_func(self.CHECK_INTERVAL)
                continue
            try:
                connection.readloop()
            except socket.error:
                connection.disconnect()
                self._conn_check(connection)
            except ConnectionError:
                connection.disconnect()
                self._conn_check(connection)
            except:
                connection.disconnect()
                self._conn_check(connection)
            finally:
                pool.release(connection)

    def _conn_check(self, connection):
        while 1:
            try:
                connection.connect()
                break
            except socket.error:
                sleep_func(self.CHECK_INTERVAL)
            except ConnectionError:
                sleep_func(self.CHECK_INTERVAL)
            finally:
                sleep_func(self.CHECK_INTERVAL)

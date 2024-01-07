from __future__ import annotations

from multiprocessing import Process
from os import kill as _kill, getpid
from pickle import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from tkinter import Tk
from typing import Callable, ParamSpec, Iterable, Generic, TypeVar, ContextManager

try:
    # UNIX
    from signal import SIGKILL as __sig1, SIGABRT as __sig2, SIGTERM as __sig3
except ImportError:
    # WIN
    from signal import SIGBREAK as __sig1, SIGABRT as __sig2, SIGTERM as __sig3

_killsigs = (__sig1, __sig2, __sig3)

_P = ParamSpec("_P")
_R = TypeVar("_R")


class TkBgReceiver(ContextManager, Generic[_R]):
    """
    This Receiver object is returned by a function decorated with :class:`TkBgServer`.
    It can be used to receive the values from the process.

    Can be used as a context manager to automatically close the server and the connection after leaving.

    .. code::

        with <decorated function>() as recv:
            value = recv.receive(block=True)
        ...
    """

    server: TkBgServer
    sock: socket

    def __init__(
            self,
            server: TkBgServer,
    ):
        self.server = server
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.connect(server.server_address)

    def close_connection(self):
        """Send the shutdown signal and close the socket."""
        try:
            self.sock.shutdown(SHUT_RDWR)
        except OSError as e:
            if e.errno != 107:  # Transport endpoint is not connected
                raise
        self.sock.close()

    def kill_server(self):
        """
        Kill the server process by the sequence
            - SIGKILL (UNIX) / SIGABRT (WINDOWS)
            - SIGTERM
            - SIGBREAK
        """
        pid = self.server.process.pid
        for sig in _killsigs:
            _kill(pid, sig)

    def terminate_server(self):
        """Terminate the server process by SIGTERM, send the shutdown signal and close the socket."""
        self.server.process.terminate()
        self.close_connection()

    def receive(self, block: bool = False, block_value: object = None) -> _R:
        """Receive a value from the socket."""
        self.sock.setblocking(block)
        try:
            data = b''
            while _data := self.sock.recv(1024):
                data += _data
            return loads(data)
        except BlockingIOError:
            return block_value

    def __delete__(self):
        self.close_connection()

    def __enter__(self) -> TkBgReceiver:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate_server()


class TkBgServer(Generic[_P, _R]):
    """This **wrap** is created by ``TkBgWrapper``."""

    make: Callable[[TkBgServer, _P], Tk]
    tk: Tk
    sock: socket | None
    instand_return: bool
    instand_block: bool
    process_daemon: bool
    process: Process
    address_pool: tuple[tuple[str, int]] | None
    server_address: tuple[str, int] | None

    def send(self, obj: _R):
        """Send a pickable object via the socket."""
        if self.sock:
            conn, addr = self.sock.accept()
            return conn.send(dumps(obj))

    @staticmethod
    def kill_process():
        """
        Kill this process by the sequence
            - SIGKILL (UNIX) / SIGABRT (WINDOWS)
            - SIGTERM
            - SIGBREAK
        """
        pid = getpid()
        for sig in _killsigs:
            _kill(pid, sig)

    def open_socket(self):
        """Open a new socket."""
        if self.address_pool:
            for addr in self.address_pool:
                try:
                    self.sock = socket(AF_INET, SOCK_STREAM)
                    self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                    self.sock.bind(addr)
                    self.sock.listen(1)
                    self.server_address = addr
                    return
                except OSError as e:
                    if e.errno != 98:  # Address already in use
                        raise
            else:
                self.close_socket()
                err = OSError(f"All address already in use: {self.address_pool}")
                err.errno = 98
                raise err

    def close_socket(self):
        """Close the socket."""
        if self.sock:
            try:
                self.sock.shutdown(SHUT_RDWR)
            except OSError as e:
                if e.errno != 107:  # Transport endpoint is not connected
                    raise
            self.sock.close()
            self.sock = self.server_address = None

    def kill_tk(self):
        """self.tk.destroy()"""
        self.tk.destroy()

    def exit(self):
        """Destroy <tk> and close the socket."""
        self.kill_tk()
        self.close_socket()

    def __delete__(self):
        self.close_socket()

    def __init__(
            self,
            make: Callable[[TkBgServer, _P], Tk],
            address_pool: tuple[tuple[str, int]] | tuple | None = ("127.0.0.11", 50_000),
            process_daemon: bool = True,
            instand_return: bool = False,
            instand_return_blocking: bool = True,
    ):
        self.make = make
        self.address_pool = address_pool
        self.sock = self.server_address = None
        self.instand_return = instand_return
        self.instand_block = instand_return_blocking
        self.process_daemon = process_daemon

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> TkBgReceiver[_R] | object:
        if not self.sock:
            self.open_socket()

        def proc(*_args, **_kwargs):
            self.tk = self.make(*_args, **_kwargs | dict(server=self))
            self.tk.mainloop()
            try:
                self.send(None)
            except OSError as e:
                if e.errno != 9:  # Receiver closed
                    raise
            return

        self.process = Process(target=proc, args=args, kwargs=kwargs, daemon=self.process_daemon)

        if self.sock:
            recv = TkBgReceiver(self)
            self.process.start()

            if self.instand_return:
                return recv.receive(self.instand_block)
            else:
                return recv

        else:
            self.process.start()
            return None


def TkBgWrapper(
        address: tuple[str, int] | Iterable[tuple[str, int]] | tuple | None = ("127.0.0.11", 50_000),
        process_daemon: bool = True,
        instand_return: bool = False,
        instand_return_blocking: bool = True,
):
    """
    This **decorator** is for executing the Tk mainloop in a separate
    process.

    This avoids some errors that occur during re-execution.
    In addition, the widget is executed independently of other (Tk)
    processes.

    The decorated function (ff. function) is wrapped in :class:`TkBgServer`.

    The function must return a Tk object that supports the ``.mainloop()``
    method. In addition, this function must have a keyword-accessible
    parameter named `server`. Here the :class:`TkBgServer` is passed.

    The transmission of values from the function is done via a socket
    by ``server.send(<obj>)``, the object must be **pickable**.

    By default, the socket is only created when the decorated function
    is called, but can be created at any time by ``.open_socket()``.
    For better compatibility, a pool of available addresses can be
    defined.

    By default, the :class:`TkBgReceiver` is returned when the decorated
    function is executed.
    If `instand_return` is set to True, the first returned value from
    the function is returned instead;
    `instand_return_blocking` then defines the blocking when receiving
    the value.

    If `address` is None or empty, the socket is never created and there
    is no possibility to get values from the process via
    :class:`TkBgReceiver`. In this case, the decorated function
    immediately returns None.

    ````

    Example 1:

        .. code::

            @TkBgWrapper()
            def func(server: TkBgServer):

                tk = Tk()

                ...

                def finally(<value>):
                    server.send(<value>)
                    server.exit()

                tk.bind(<finally>, lambda e: finally(<value>))

                tk.bind(<send>, lambda e: server.send(<value>))

                tk.bind(<exit>, lambda e: server.exit())

                return tk

            receiver = func()

            while <cond>:
                value = receiver.receive(block=False)
                if value:
                    ...
                ...

    ````

    Example 2:

        .. code::

            @TkBgWrapper(instand_return=True)
            def func(server: TkBgServer):

                tk = Tk()

                ...

                def finally(<value>):
                    server.send(<value>)
                    server.exit()

                tk.bind(<finally>, lambda e: finally(<value>))

                return tk

            value = func()
            ...
    """
    if address:
        if not isinstance(address[0], tuple):
            address_pool = (address,)
        else:
            address_pool = tuple(address)
    else:
        address_pool = None

    def wrap(make: Callable[[TkBgServer, _P], Tk]) -> TkBgServer[_P]:
        return TkBgServer(make, address_pool, process_daemon, instand_return, instand_return_blocking)

    return wrap

from typing import Any

from PySide6.QtCore import QObject, QByteArray
from PySide6.QtNetwork import QTcpServer, QTcpSocket, QAbstractSocket, QHostAddress

from .jsonrpc import JSONRPCProvider


class RPCInterface(JSONRPCProvider):

    def __init__(self):
        super().__init__()
        self.add_method(self.echo)
        self.add_method(self.return_, alias="return")
        self.add_method(self.disappear)
        self.add_method(self.hello)

    def hello(self, name="World"):
        return f"Hello {name}!"

    def echo(self, s: str):
        print("ECHO:", s)

    def return_(self, x: Any):
        return x

    def disappear(self):
        self.remove_method(self.toggle)


class Server(QTcpServer):

    interface: JSONRPCProvider

    def __init__(self, interface: JSONRPCProvider | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self.interface = interface if interface else RPCInterface()
        self.newConnection.connect(self._handle_new_connection)

    def run(self, address: QHostAddress = QHostAddress.Any, port: int = 0) -> bool:
        if not self.listen(address, port):
            print(f"Failed to start QuahlTcpServer on {address}:{port}")
            return False
        print(f"QuahlTcpServer listening on {self.serverAddress()}:{self.serverPort()}")

    def quit(self):
        self.close()

    def _handle_new_connection(self):
        connection = self.nextPendingConnection()
        if not connection:
            print("Connection was incoming but is not available...")
            return
        self._cx = ConnectionHandler(connection, self.interface, self)


class ConnectionHandler(QObject):

    buffer: QByteArray = QByteArray()

    def __init__(self, socket: QTcpSocket, interface: RPCInterface, parent: QObject | None = None):
        super().__init__(parent)
        self._interface = interface
        self._socket = socket
        print("Sock parent:", self._socket.parent(), "Server:", parent)
        self._socket.readyRead.connect(self._handle_new_data)
        print(
            "New socket handler initiated.\n"
            f"State: {self.socket_state_to_str(socket.state())}.\n"
            f"Peer: {socket.peerAddress()}:{socket.peerPort()} (named? {socket.peerName()})."
        )
        self._handle_new_data()
        self._socket.write(b"Hello from Quahl!\r\n")

    def socket_state_to_str(self, socket_state: QAbstractSocket.SocketState):
        states = {
            QAbstractSocket.UnconnectedState: "unconnected",
            QAbstractSocket.HostLookupState: "performing host name lookup",
            QAbstractSocket.ConnectingState: "establishing connection",
            QAbstractSocket.ConnectedState: "connected",
            QAbstractSocket.BoundState: "bound",
            QAbstractSocket.ClosingState: "about to close",
            QAbstractSocket.ListeningState: "listening",
        }
        return states[socket_state]

    def _handle_new_data(self):
        while b := self._socket.read(1):
            self.buffer.append(b)
            if self.buffer.endsWith(b"\r\n\r\n"):
                self._execute_buffer()

    def _execute_buffer(self):
        buffered = self.buffer.data()
        self.buffer.clear()
        if not buffered:
            return
        result = self._interface.process_request(buffered)
        if result:
            self._socket.write(result)
            self._socket.write(b"\r\n\r\n")
            self._socket.flush()

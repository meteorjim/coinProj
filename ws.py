import socket
from urllib.parse import urlparse

# make sure PySocks(https://github.com/Anorov/PySocks) is installed, commit version >= 1f56ca
import socks
import ssl

# make sure ws4py is installed, version >= 0.4.2
from ws4py.exc import HandshakeError
from ws4py.client import WebSocketBaseClient


def connect(self):
    """
    Connects this websocket and starts the upgrade handshake
    with the remote endpoint.
    """
    # https://stackoverflow.com/questions/16136916/using-socksipy-with-ssl
    self.sock.connect(self.bind_addr)

    if self.scheme == "wss":
        # default port is now 443; upgrade self.sender to send ssl
        self.sock = ssl.wrap_socket(self.sock, **self.ssl_options)
        self._is_secure = True

    self._write(self.handshake_request)

    response = b''
    doubleCLRF = b'\r\n\r\n'
    while True:
        bytes = self.sock.recv(128)
        if not bytes:
            break
        response += bytes
        if doubleCLRF in response:
            break

    if not response:
        self.close_connection()
        raise HandshakeError("Invalid response")

    headers, _, body = response.partition(doubleCLRF)
    response_line, _, headers = headers.partition(b'\r\n')

    try:
        self.process_response_line(response_line)
        self.protocols, self.extensions = self.process_handshake_header(headers)
    except HandshakeError:
        self.close_connection()
        raise

    self.handshake_ok()
    if body:
        self.process(body)


WebSocketBaseClient.connect = connect


class ProxyHelper:
    def __init__(self, proxy):
        """
        :param proxy: could be socks4/socks5/http proxy
                      example: socks5://127.0.0.1:8080
        """

        self.url = urlparse(proxy)
        schema = self.url.scheme.upper()
        assert schema in socks.PROXY_TYPES, "%s is not a supported proxy type" % schema
        self.proxy_type = socks.PROXY_TYPES[schema]

    def patch(self, websocket_client, rdns=True):
        """
        :param websocket_client: initialized client instance
        :param rdns: if to query dns with proxy
        """
        origin = websocket_client.sock

        s = socks.socksocket(
            family=origin.family,
            type=origin.type,
            proto=origin.proto,
        )

        s.set_proxy(
            proxy_type=self.proxy_type,
            addr=self.url.hostname,
            port=int(self.url.port) if self.url.port else None,
            rdns=rdns,
            username=self.url.username,
            password=self.url.password
        )

        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if hasattr(socket, 'AF_INET6') and origin.family == socket.AF_INET6 and \
            websocket_client.host.startswith('::'):
            try:
                s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except (AttributeError, socket.error):
                pass

        websocket_client.sock = s


if __name__ == '__main__':
    from ws4py.client.geventclient import WebSocketClient
    import datetime

    ws = WebSocketClient('wss://api-aws.huobi.pro/ws', ssl_options={"cert_reqs": 0})
    # support socks4/socks5/http proxy, make sure http proxy support CONNECT
    proxy_helper = ProxyHelper("socks5://127.0.0.1:12315")
    proxy_helper.patch(ws, False)
    ws.connect()

    resp = ws.send({"ping":int(datetime.datetime.now().timestamp())})
    print(resp)

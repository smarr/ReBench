try:
    # Python 3
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import socket
from threading import Thread


_put_requests = 0


class _RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_PUT(self):
        self.send_response(200)
        self.end_headers()
        global _put_requests  # pylint: disable=global-statement
        _put_requests += 1

    def log_request(self, code='-', size='-'):
        pass


class MockHTTPServer(object):

    def __init__(self):
        self._port = -1
        self._server = None
        self._thread = None

    def get_free_port(self):
        s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
        s.bind(('localhost', 0))
        _address, port = s.getsockname()
        s.close()

        self._port = port
        return port

    def start(self):
        self._server = HTTPServer(('localhost', self._port), _RequestHandler)

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.setDaemon(True)
        self._thread.start()

    def shutdown(self):
        self._server.shutdown()

    def get_number_of_put_requests(self):
        global _put_requests  # pylint: disable=global-statement
        return _put_requests

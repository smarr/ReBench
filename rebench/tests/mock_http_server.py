import socket

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from time import sleep


class _RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(self.server.status_code)
        self.end_headers()
        self.send_header("Content-Length", 0)
        self.server.get_requests += 1

    def do_PUT(self):
        self.send_response(self.server.status_code)
        self.send_header("Content-Length", 0)
        self.end_headers()
        self.server.put_requests += 1

    def do_OPTIONS(self):
        self.send_response(self.server.status_code)
        if self.server.api_v2:
            self.send_header("X-ReBenchDB-Result-API-Version", "2.0.0")
        self.send_header("Allow", "PUT")
        self.send_header("Content-Length", 0)
        self.end_headers()
        self.server.options_requests += 1

    def log_request(self, code="-", size="-"):
        pass


class HTTPServerWithCounter(HTTPServer):
    def __init__(self, *args, **kwargs):
        super(HTTPServerWithCounter, self).__init__(*args, **kwargs)
        self.put_requests = 0
        self.get_requests = 0
        self.options_requests = 0
        self.api_v2 = None
        self.status_code = 200


class MockHTTPServer(object):

    def __init__(self, api_v2 = True, test_error_handling = False):
        self._port = -1
        self._server = None
        self._thread = None
        self._is_shutdown = False
        self.api_v2 = api_v2
        self._test_error_handling = test_error_handling

    def get_free_port(self):
        s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
        s.bind(("localhost", 0))
        _address, port = s.getsockname()
        s.close()

        self._port = port
        return port

    def start(self):
        self._server = HTTPServerWithCounter(("localhost", self._port), _RequestHandler)
        self._server.api_v2 = self.api_v2
        if self._test_error_handling:
            self._server.status_code = 400

        self._thread = Thread(target=self._server.serve_forever)
        self._thread.daemon = True
        self._thread.start()

    def process_and_shutdown(self):
        if self._is_shutdown:
            return

        sleep(1)  # yield GIL and give server time to process request

        self._is_shutdown = True
        self._server.shutdown()

    def get_number_of_put_requests(self):
        result = self._server.put_requests
        self._server.put_requests = 0
        return result

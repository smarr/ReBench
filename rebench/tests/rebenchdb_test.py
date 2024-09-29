from .mock_http_server import MockHTTPServer
from .rebench_test_case import ReBenchTestCase
from ..rebenchdb import ReBenchDB


class ReBenchDBTest(ReBenchTestCase):
    def test_is_api_v2(self):
        server = MockHTTPServer()
        try:
            port = server.get_free_port()
            server.start()

            db = ReBenchDB("http://localhost:" + str(port), "project", "experiment", self.ui)
            self.assertTrue(db.is_api_v2())
        finally:
            server.process_and_shutdown()

    def test_is_api_v2_on_server_without_v2_support(self):
        server = MockHTTPServer(False)
        try:
            port = server.get_free_port()
            server.start()

            db = ReBenchDB("http://localhost:" + str(port), "project", "experiment", self.ui)
            self.assertFalse(db.is_api_v2())
        finally:
            server.process_and_shutdown()

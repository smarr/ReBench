import json
from datetime import datetime

from .ui import UIError

try:
    from http.client import HTTPException
    from urllib.request import urlopen, Request as PutRequest
except ImportError:
    # Python 2.7
    from httplib import HTTPException
    from urllib2 import urlopen, Request


    class PutRequest(Request):
        def __init__(self, *args, **kwargs):
            if 'method' in kwargs:
                del kwargs['method']
            Request.__init__(self, *args, **kwargs)

        def get_method(self, *_args, **_kwargs):  # pylint: disable=arguments-differ
            return 'PUT'


def get_current_time():
    """Return the current time as string for use with ReBenchDB and other persistency backends."""
    return datetime.utcnow().isoformat() + "+00:00"


class ReBenchDB(object):

    def __init__(self, server_base_url, project_name, experiment_name, ui):
        self._ui = ui

        if not server_base_url:
            raise UIError("ReBenchDB expected server address, but got: %s" % server_base_url, None)

        # A user warning that old style configuration is detected
        if server_base_url.endswith('/results'):
            raise UIError(
                "The URL to ReBenchDB should exclude '/results' but was '%s'" % server_base_url,
                None)

        ui.debug_output_info(
            'ReBench will report all measurements to {url}\n', url=server_base_url)

        self._server_base_url = server_base_url
        self._project_name = project_name
        self._experiment_name = experiment_name

    def send_results(self, benchmark_data, num_measurements):
        success, response = self._send_to_rebench_db(benchmark_data, '/results')

        if success:
            self._ui.verbose_output_info(
                "ReBenchDB: Sent {num_m} results to ReBenchDB, response was: {resp}\n",
                num_m=num_measurements, resp=response)

        return success, response

    def send_completion(self, end_time):
        success, response = self._send_to_rebench_db({'endTime': end_time}, '/completion')

        if success:
            self._ui.verbose_output_info(
                "ReBenchDB was notified of completion of {project} {exp} at {time}\n" +
                "{ind} Its response was: {resp}\n",
                project=self._project_name, exp=self._experiment_name, time=end_time, resp=response)
        else:
            self._ui.error("Reporting completion to ReBenchDB failed.\n" +
                           "{ind}Error: {response}", response=response)

        return success, response

    @staticmethod
    def _send_payload(payload, url):
        req = PutRequest(url, payload,
                         {'Content-Type': 'application/json'}, method='PUT')
        socket = urlopen(req)
        response = socket.read()
        socket.close()
        return response

    def _send_to_rebench_db(self, payload_data, operation):
        payload_data['projectName'] = self._project_name
        payload_data['experimentName'] = self._experiment_name
        url = self._server_base_url + operation

        payload = json.dumps(payload_data, separators=(',', ':'), ensure_ascii=True)

        # self._ui.output("Saving JSON Payload of size: %d\n" % len(payload))
        with open("payload.json", "w") as text_file:
            text_file.write(payload)

        try:
            data = payload.encode('utf-8')
            response = self._send_payload(data, url)
            return True, response
        except TypeError as te:
            self._ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                           + "{ind}{ind}" + str(te) + "\n")
        except (IOError, HTTPException):
            # network or server may have issues, let's try one more time
            try:
                response = self._send_payload(payload, url)
                return True, response
            except (IOError, HTTPException) as error:
                self._ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                               + "{ind}{ind}" + str(error) + "\n")
        return False, None

import json
from datetime import datetime
from time import sleep

from http.client import HTTPException
from urllib.request import urlopen, Request as PutRequest

from .ui import UIError


def get_current_time():
    """Return the current time as string for use with ReBenchDB and other persistency backends."""
    return datetime.utcnow().isoformat() + "+00:00"


class ReBenchDB(object):

    def __init__(self, server_base_url, project_name, experiment_name, ui):
        self.ui = ui

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

    def send_results(self, benchmark_data, num_items):
        success, response = self._send_to_rebench_db(benchmark_data, '/results')

        if success:
            self.ui.verbose_output_info(
                "ReBenchDB: Sent {num_i} results to ReBenchDB, response was: {resp}\n",
                num_i=num_items, resp=response)

        return success, response

    def send_completion(self, end_time):
        success, response = self._send_to_rebench_db({'endTime': end_time}, '/completion')

        if success:
            self.ui.verbose_output_info(
                "ReBenchDB was notified of completion of {project} {exp} at {time}\n" +
                "{ind} Its response was: {resp}\n",
                project=self._project_name, exp=self._experiment_name, time=end_time, resp=response)
        else:
            self.ui.error("Reporting completion to ReBenchDB failed.\n" +
                           "{ind}Error: {response}", response=response)

        return success, response

    @staticmethod
    def _send_payload(payload, url):
        req = PutRequest(url, payload,
                         {'Content-Type': 'application/json'}, method='PUT')
        with urlopen(req) as socket:
            response = socket.read()
            return response

    def _send_to_rebench_db(self, payload_data, operation):
        payload_data['projectName'] = self._project_name
        payload_data['experimentName'] = self._experiment_name
        url = self._server_base_url + operation

        payload = json.dumps(payload_data, separators=(',', ':'), ensure_ascii=True)

        # self.ui.output("Saving JSON Payload of size: %d\n" % len(payload))
        with open("payload.json", "w") as text_file:  # pylint: disable=unspecified-encoding
            text_file.write(payload)

        return self._send_with_retries(payload.encode('utf-8'), url)

    def _send_with_retries(self, payload_bytes, url):
        attempts = 4
        wait_sec = 10
        while True:
            try:
                response = self._send_payload(payload_bytes, url)
                return True, response
            except TypeError as te:
                # can't handle this, just abort
                self.ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                               + "{ind}{ind}" + str(te) + "\n")
                return False, None
            except (IOError, HTTPException) as error:
                if attempts > 0:
                    # let's retry, the benchmark server might just time out, as usual
                    # but let it breath a little
                    self.ui.verbose_output_info(
                        "ReBenchDB: had issue reporting data. Trying again after "
                        + str(wait_sec) + "seconds.\n"
                        + "{ind}{ind}" + str(error) + "\n")
                    attempts -= 1
                    sleep(wait_sec)
                    wait_sec *= 2
                else:
                    self.ui.error("{ind}Error: Reporting to ReBenchDB failed.\n"
                                   + "{ind}{ind}" + str(error) + "\n")
                    return False, None

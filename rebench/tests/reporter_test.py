from .rebench_test_case import ReBenchTestCase

from ..configurator import Configurator, load_config
from ..executor import Executor
from ..persistence import DataStore
from ..rebench import ReBench
from ..reporter import CodespeedReporter

try:
    from http.client import HTTPException
except ImportError:
    from httplib import HTTPException


class ReporterTest(ReBenchTestCase):

    def _run_benchmarks_and_do_reporting(self):
        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args([
            '--commit-id=id', '--environment=test', '--project=test', 'persistency.conf'])
        cnf = Configurator(load_config(self._path + '/persistency.conf'), DataStore(self._ui),
                           self._ui, cmd_config, data_file=self._tmp_file)

        self._runs = cnf.get_runs()  # pylint: disable=attribute-defined-outside-init

        ex = Executor(self._runs, False, self._ui)
        ex.execute()
        reporter = cnf.reporting.codespeed_reporter
        reporter.report_job_completed(self._runs)

    def test_send_to_codespeed(self):
        sent_results = [False]

        def _send_to_codespeed(_reporter, _results, run_id):
            self.assertIn(run_id, self._runs)
            sent_results[0] = True

        original_send_to = CodespeedReporter._send_to_codespeed
        CodespeedReporter._send_to_codespeed = _send_to_codespeed

        try:
            self._run_benchmarks_and_do_reporting()
            self.assertTrue(sent_results[0])
        finally:
            CodespeedReporter._send_to_codespeed = original_send_to

    def test_send_to_codespeed_with_error(self):
        sent_results = [False]

        def _send_payload(_reporter, _payload):
            sent_results[0] = True
            raise HTTPException()

        old_send_payload = CodespeedReporter._send_payload
        CodespeedReporter._send_payload = _send_payload

        try:
            self._run_benchmarks_and_do_reporting()
            self.assertTrue(sent_results[0])
        finally:
            CodespeedReporter._send_payload = old_send_payload

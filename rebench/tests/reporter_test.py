from http.client import HTTPException

from .rebench_test_case import ReBenchTestCase

from ..configurator import Configurator, load_config
from ..executor import Executor
from ..persistence import DataStore
from ..rebench import ReBench
from ..reporter import CodespeedReporter, TextReporter


class ReporterTest(ReBenchTestCase):

    def _run_benchmarks_and_do_reporting(self, rebench_db=True):
        option_parser = ReBench().shell_options()
        if rebench_db:
            args = ['--commit-id=id', '--environment=test', '--project=test', 'persistency.conf']
            config = load_config(self._path + '/persistency.conf')
        else:
            args = ['-R', 'test.conf', 'Test']
            config = load_config(self._path + '/test.conf')

        cmd_config = option_parser.parse_args(args)
        cnf = Configurator(config, DataStore(self.ui),
                           self.ui, cmd_config, data_file=self._tmp_file)

        self._runs = cnf.get_runs()  # pylint: disable=attribute-defined-outside-init

        ex = Executor(self._runs, False, self.ui)
        ex.execute()

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

    def test_text_reporter_summary_table(self):
        self._run_benchmarks_and_do_reporting(False)
        reporter = TextReporter()
        sorted_rows, used_cols, summary = reporter._generate_all_output(self._runs)
        self.assertEqual(38, len(sorted_rows))
        self.assertEqual(len(reporter.expected_columns) - 1, len(sorted_rows[0]))
        self.assertEqual(['Benchmark', 'Executor', 'Suite', 'Extra', 'Core', 'Size', 'Var',
             'Machine', 'Mean (ms)'], used_cols)
        self.assertEqual('#Samples', summary[0][0])
        self.assertEqual(0, summary[0][1])

    def test_text_reporter_summary_table_4_runs(self):
        self._run_benchmarks_and_do_reporting(False)
        reporter = TextReporter()

        filter_runs = list(self._runs)[:4]

        sorted_rows, used_cols, summary = reporter._generate_all_output(filter_runs)
        self.assertEqual(4, len(sorted_rows))
        self.assertEqual(reporter.expected_columns, used_cols)
        self.assertIsNone(summary)

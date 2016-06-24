from ...configurator import Configurator
from ...executor     import Executor
from ...reporter     import Reporter
from ..rebench_test_case import ReBenchTestCase

from rebench import reporter


class TestReporter(Reporter):

    def __init__(self, cfg):
        super(TestReporter, self).__init__()
        self._run_failed    = []
        self._run_completed = []
        self._job_completed = []

    def run_failed(self, run_id, _cmdline, _return_code, _output):
        self._run_failed.append(run_id)

    def run_completed(self, run_id, statistics, cmdline):
        self._run_completed.append(run_id)

    def report_job_completed(self, run_ids):
        self._job_completed.append(run_ids)


class Issue38BasicIRCReporting(ReBenchTestCase):

    def setUp(self):
        super(Issue38BasicIRCReporting, self).setUp(__file__)
        reporter.IrcReporter = TestReporter  # mock the IrcReporter for testing

    def _get_test_reporter(self, run):
        rep = list(run._reporters)

        self.assertEqual(2, len(rep))
        test_rep = rep[0] if isinstance(rep[0], TestReporter) else rep[1]
        self.assertTrue(isinstance(test_rep, TestReporter))
        return test_rep

    def test_get_expected_notifications(self):
        cnf = Configurator(self._path + '/issue_38.conf',
                           standard_data_file = self._tmp_file)
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.bench_cfg.name)

        ex = Executor(runs, False, False)
        ex.execute()

        test_rep = self._get_test_reporter(runs[0])
        self.assertEqual(test_rep, self._get_test_reporter(runs[1]))
        self.assertEqual(test_rep, self._get_test_reporter(runs[2]))

        self.assertEqual(1, len(test_rep._job_completed))
        self.assertEqual(6, len(test_rep._run_failed))

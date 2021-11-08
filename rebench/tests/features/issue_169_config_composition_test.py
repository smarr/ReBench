from ..rebench_test_case import ReBenchTestCase
from ...configurator import Configurator, load_config
from ...persistence import DataStore


class Issue169ConfigCompositionTest(ReBenchTestCase):

    def setUp(self):
        super(Issue169ConfigCompositionTest, self).setUp()
        self._set_path(__file__)
        self.cnf = Configurator(
            load_config(self._path + '/issue_169.conf'),
            DataStore(self.ui), self.ui, None, 'all')
        self.runs = list(self.cnf.get_runs())
        self.runs = sorted(self.runs, key=lambda e: e.cmdline())

        self.cnf_important = Configurator(
            load_config(self._path + '/issue_169_important.conf'),
            DataStore(self.ui), self.ui, None, 'all')
        self.runs_important = list(self.cnf_important.get_runs())
        self.runs_important = sorted(self.runs_important, key=lambda e: e.cmdline())

    def _assert(self, run, exe, bench, iterations, invocations):
        self.assertEqual(run.benchmark.suite.executor.name, exe)
        self.assertEqual(run.benchmark.name, bench)
        self.assertEqual(run.iterations, iterations)
        self.assertEqual(run.invocations, invocations)

    def test_confirm_setting_priority(self):
        self._assert(self.runs[0], "TestRunner1", "Bench1", 40, 1)
        self._assert(self.runs[1], "TestRunner1", "Bench2", 30, 1)

        self._assert(self.runs[2], "TestRunner2", "Bench1", 40, 1)
        self._assert(self.runs[3], "TestRunner2", "Bench2", 30, 1)
        self._assert(self.runs[4], "TestRunner2", "Bench3", 10, 3)
        self._assert(self.runs[5], "TestRunner2", "Bench4", 10, 1)

    def test_confirm_setting_priority_with_important_settings(self):
        self._assert(self.runs_important[0], "TestRunner1", "Bench1", 30, 1)
        self._assert(self.runs_important[1], "TestRunner1", "Bench2", 30, 1)

        self._assert(self.runs_important[2], "TestRunner2", "Bench1", 30, 2)
        self._assert(self.runs_important[3], "TestRunner2", "Bench2", 30, 2)
        self._assert(self.runs_important[4], "TestRunner2", "Bench3", 10, 3)
        self._assert(self.runs_important[5], "TestRunner2", "Bench4", 10, 2)

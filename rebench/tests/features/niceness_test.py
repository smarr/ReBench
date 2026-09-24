from os import nice

from ...configurator import Configurator, parse_config
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase, make_executor_cls

_CONFIG = """
default_experiment: WithNice

runs:
  invocations: 2

benchmark_suites:
    Suite:
        gauge_adapter: Multivariate
        command: TestBenchMarks %(benchmark)s
        benchmarks:
            - Bench1

executors:
    TestRunner1:
        path: .
        executable: niceness_vm.py

experiments:
    WithNice:
        suites:
         - Suite
        executions:
         - TestRunner1
    WithoutNice:
        suites:
         - Suite
        executions:
         - TestRunner1
        denoise:
            use_nice: false
"""


class NicenessTest(ReBenchTestCase):
    """
    Confirm that niceness was set in the benchmark process.
    """

    def setUp(self):
        super(NicenessTest, self).setUp()
        self._set_path(__file__)
        self._initial_settings = self._get_initial_denoise_settings_and_ensure_cleanup()

    def _execute_and_get_niceness(self, exp_name):
        cnf = Configurator(
            parse_config(_CONFIG),
            DataStore(self.ui),
            self.ui,
            exp_name=exp_name,
            data_file=self._tmp_file,
        )
        runs = list(cnf.get_runs())
        self.assertEqual(len(runs), 1)

        DebugExecutor, all_outputs, _ = make_executor_cls()
        ex = DebugExecutor(
            runs, False, self.ui, initials_and_capabilities=self._initial_settings
        )
        ex.execute()

        self.assertEqual(runs[0].get_number_of_data_points(), 2)
        self.assertEqual(len(all_outputs), 2)

        niceness = []
        for output in all_outputs:
            for line in output.splitlines():
                if line.startswith("Benchmark Niceness:"):
                    niceness.append(int(line.split(":")[1].strip()))

        self.assertEqual(len(niceness), 2)
        return niceness

    def test_niceness_is_set(self):
        if self._initial_settings.can_set_nice is not True:
            self.skipTest("rebench-denoise cannot set niceness on this machine")

        niceness = self._execute_and_get_niceness("WithNice")
        self.assertEqual(niceness, [-20, -20])

    def test_niceness_is_unchanged_without_use_nice(self):
        current_niceness = nice(0)
        niceness = self._execute_and_get_niceness("WithoutNice")
        self.assertEqual(niceness, [current_niceness, current_niceness])

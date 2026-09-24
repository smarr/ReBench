from ...configurator import Configurator, parse_config
from ...denoise_client import get_initial_settings_and_capabilities
from ...model.denoise import Denoise
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase, make_executor_cls

_CONFIG = """
default_experiment: WithNoTurbo
runs: {invocations: 2}

benchmark_suites:
    Suite:
        gauge_adapter: Multivariate
        command: TestBenchMarks %(benchmark)s
        benchmarks: [Bench1]

executors:
    TestRunner1: {path: ., executable: no_turbo_vm.py}

experiments:
    WithNoTurbo: {suites: [Suite], executions: [TestRunner1]}
    WithTurbo: {suites: [Suite], executions: [TestRunner1], denoise: {no_turbo: false}}
"""


class NoTurboTest(ReBenchTestCase):
    """
    Check whether turbo boost is disabled from the view of the benchmark process.
    """

    def setUp(self):
        super(NoTurboTest, self).setUp()
        self._set_path(__file__)

        self._initial_settings = get_initial_settings_and_capabilities(
            False, self.ui, Denoise.default()
        )

        if self._initial_settings.can_set_no_turbo is not True:
            self.skipTest("rebench-denoise cannot disable turbo boost on this machine")

    def _execute_and_get_turbo_boost_disabled(self, exp_name):
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

        turbo_boost_disabled = []
        for output in all_outputs:
            for line in output.splitlines():
                if line.startswith("Benchmark Turbo Boost Disabled:"):
                    turbo_boost_disabled.append(line.split(":")[1].strip())

        self.assertEqual(len(turbo_boost_disabled), 2)
        return turbo_boost_disabled

    def test_turbo_boost_is_disabled(self):
        disabled = self._execute_and_get_turbo_boost_disabled("WithNoTurbo")
        self.assertEqual(disabled, ["True", "True"])

    def test_turbo_boost_is_enabled_with_no_turbo_false(self):
        disabled = self._execute_and_get_turbo_boost_disabled("WithTurbo")
        self.assertEqual(disabled, ["False", "False"])

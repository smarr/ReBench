from ...configurator import Configurator, parse_config
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase, make_executor_cls

_CONFIG = """
default_experiment: WithPerformance
runs: {invocations: 2}

benchmark_suites:
    Suite:
        gauge_adapter: Multivariate
        command: TestBenchMarks %(benchmark)s
        benchmarks: [Bench1]

executors:
    TestRunner1: {path: ., executable: scaling_governor_vm.py}

experiments:
    WithPerformance: {suites: [Suite], executions: [TestRunner1]}
    WithPowersave:
        suites: [Suite]
        executions: [TestRunner1]
        denoise: {scaling_governor: powersave}
"""


class ScalingGovernorTest(ReBenchTestCase):
    """
    Check the scaling governor from the view of the benchmark process.
    """

    def setUp(self):
        super(ScalingGovernorTest, self).setUp()
        self._set_path(__file__)
        self._initial_settings = self._get_initial_denoise_settings_and_ensure_cleanup()

        if self._initial_settings.can_set_scaling_governor is not True:
            self.skipTest(
                "rebench-denoise cannot set the scaling governor on this machine"
            )

    def _execute_and_get_scaling_governor(self, exp_name):
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

        governors = []
        for output in all_outputs:
            for line in output.splitlines():
                if line.startswith("Benchmark Scaling Governor:"):
                    governors.append(line.split(":")[1].strip())

        self.assertEqual(len(governors), 2)
        return governors

    def test_performance_governor_is_set(self):
        governors = self._execute_and_get_scaling_governor("WithPerformance")
        self.assertEqual(governors, ["performance", "performance"])

    def test_powersave_governor_is_set_when_requested(self):
        governors = self._execute_and_get_scaling_governor("WithPowersave")
        self.assertEqual(governors, ["powersave", "powersave"])

from ...configurator import Configurator, load_config
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase


class RunIdTest(ReBenchTestCase):
    def setUp(self):
        super(RunIdTest, self).setUp()
        self._cnf = Configurator(
            load_config(self._path + "/model/run_id_test.conf"),
            DataStore(self.ui),
            self.ui,
            None,
            data_file=self._tmp_file,
        )
        self._runs = sorted(list(self._cnf.get_runs()))

    def test_basic_equality(self):
        # this one is a bit silly, because get_runs() returns a set...
        num_runs = 28
        self.assertEqual(len(self._runs), num_runs)
        for i in range(0, num_runs):
            for j in range(0, num_runs):
                if i == j:
                    self.assertEqual(self._runs[i], self._runs[j])
                else:
                    self.assertNotEqual(self._runs[i], self._runs[j])

    def test_equality_with_env_settings(self):
        """We expect both, the run_id from TestRunner2 and TestRunner3 to be in the list"""
        has_test_runner2 = False
        has_test_runner3 = False

        run2 = None
        run3 = None

        for run in self._runs:
            if run.benchmark.name == "Bench1":
                if run.benchmark.suite.executor.name == "TestRunner2":
                    has_test_runner2 = True
                    run2 = run
                elif run.benchmark.suite.executor.name == "TestRunner3":
                    has_test_runner3 = True
                    run3 = run

        self.assertTrue(has_test_runner2)
        self.assertTrue(has_test_runner3)

        # trivially true, because they come out of a set
        self.assertNotEqual(run2, run3)
        self.assertNotEqual(run2.env["PATH"], run3.env["PATH"])
        self.assertNotEqual(run2.env["WORKDIR"], run3.env["WORKDIR"])

    def test_equality_with_non_cmdline_settings(self):
        """
        Even so the command line does not capture the variable_values, we expect separate run_ids.
        """
        has_var1 = False
        has_var2 = False

        run1 = None
        run2 = None

        for run in self._runs:
            if run.benchmark.name == "Bench1":
                if run.var_value == "var1":
                    has_var1 = True
                    run1 = run
                elif run.var_value == "var2":
                    has_var2 = True
                    run2 = run

        self.assertTrue(has_var1)
        self.assertTrue(has_var2)

        # trivially true, because they come out of a set
        self.assertNotEqual(run1, run2)

        self.assertNotEqual(run1.var_value, run2.var_value)

    def test_different_denoise_settings_make_difference(self):
        """
        The TestBenchmark2 experiment changes the denoise settings, so we expect separate run_ids.
        """
        has_basic_shield = False
        has_explicit_shield = False

        run1 = None
        run2 = None

        for run in self._runs:
            if (
                run.benchmark.name == "Bench1"
                and run.benchmark.suite.executor.name == "TestRunner1"
                and run.var_value == "var1"
            ):
                if run.denoise.shield == "basic":
                    has_basic_shield = True
                    run1 = run
                elif run.denoise.shield == "4,7-9":
                    has_explicit_shield = True
                    run2 = run

        self.assertTrue(has_basic_shield)
        self.assertTrue(has_explicit_shield)

        # trivially true, because they come out of a set
        self.assertNotEqual(run1, run2)

        self.assertNotEqual(run1.denoise.shield, run2.denoise.shield)
        self.assertNotEqual(run1.denoise.use_nice, run2.denoise.use_nice)

    def test_action_makes_difference(self):
        """We expect one run_id for action=profile and one for action=benchmark."""
        has_profile = False
        has_benchmark = False

        run_profile = None
        run_benchmark = None

        for run in self._runs:
            if run.benchmark.name == "Bench1":
                if run.is_profiling():
                    has_profile = True
                    run_profile = run
                else:
                    has_benchmark = True
                    run_benchmark = run

        self.assertTrue(has_profile)
        self.assertTrue(has_benchmark)

        # trivially true, because they come out of a set
        self.assertNotEqual(run_profile, run_benchmark)

        self.assertEqual(run_profile.benchmark.suite.executor.action, "profile")
        self.assertEqual(run_benchmark.benchmark.suite.executor.action, "benchmark")

    def test_as_dict(self):
        """Check that as_dict returns the expected information. This is only a very basic test."""
        self.assertEqual(
            self._runs[0].as_dict(),
            {
                "benchmark": {
                    "command": "Bench1",
                    "name": "Bench1",
                    "runDetails": {
                        "denoise": {
                            "minimize_perf_sampling": True,
                            "no_turbo": True,
                            "scaling_governor": "performance",
                            "shield": "4,7-9",
                            "use_nice": False,
                        },
                        "env": {"PATH": "/usr/bin:/bin:~/bin", "WORKDIR": "~/work"},
                        "execute_exclusively": True,
                        "invocations": 10,
                        "iterations": 1,
                        "maxInvocationTime": -1,
                        "minIterationTime": 50,
                        "retries_after_failure": 3,
                    },
                    "suite": {
                        "command": "Bench ~/suiteFolder/%(benchmark)s "
                        '-message "a string with a ~"',
                        "executor": {
                            "action": "benchmark",
                            "args": "-cp ~/foo:~/bar",
                            "executable": "vm1.py %(cores)s",
                            "name": "TestRunner1",
                            "path": "~/tests",
                            "runDetails": {
                                "denoise": {
                                    "minimize_perf_sampling": True,
                                    "no_turbo": True,
                                    "scaling_governor": "performance",
                                    "shield": "4,7-9",
                                    "use_nice": False,
                                },
                                "env": {
                                    "PATH": "/usr/bin:/bin:~/bin",
                                    "WORKDIR": "~/work",
                                },
                                "execute_exclusively": True,
                                "invocations": 10,
                                "iterations": 1,
                                "maxInvocationTime": -1,
                                "minIterationTime": 50,
                                "retries_after_failure": 3,
                            },
                            "variables": {
                                "cores": [1],
                                "input_sizes": [""],
                                "tags": [None],
                                "variable_values": [""],
                            },
                        },
                        "location": "~/tests",
                        "name": "Suite",
                    },
                    "variables": {
                        "cores": [1],
                        "input_sizes": [""],
                        "tags": [None],
                        "variable_values": ["var1", "var2"],
                    },
                },
                "cmdline": "~/tests/vm1.py 1 -cp ~/foo:~/bar Bench ~/suiteFolder/Bench1 "
                '-message "a string with a ~"',
                "cores": 1,
                "location": "~/tests",
                "varValue": "var1",
            },
        )

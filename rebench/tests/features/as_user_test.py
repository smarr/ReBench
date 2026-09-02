from getpass import getuser

from ...configurator import Configurator, load_config
from ...denoise_client import get_initial_settings_and_capabilities
from ...executor import Executor
from ...model.denoise import Denoise
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase


def make_executor_cls() -> tuple[type[Executor], list[str], list[list[str]]]:
    all_outputs = []
    all_cmds: list[list[str]] = []

    class DebugExecutor(Executor):
        def _eval_output(self, output, run_id, gauge_adapter, cmd):
            all_outputs.append(output)
            all_cmds.append(cmd)
            super(DebugExecutor, self)._eval_output(output, run_id, gauge_adapter, cmd)

    return DebugExecutor, all_outputs, all_cmds


class AsUserTest(ReBenchTestCase):
    """
    The benchmarks should be executed as the user that runs ReBench, not as root.
    """

    def setUp(self):
        super(AsUserTest, self).setUp()
        self._set_path(__file__)

        self._initial_settings = get_initial_settings_and_capabilities(
            False, self.ui, Denoise.default()
        )

    def _make_configurator_and_runs(self):
        cnf = Configurator(
            load_config(self._path + "/as_user.conf"),
            DataStore(self.ui),
            self.ui,
            data_file=self._tmp_file,
        )
        runs = list(cnf.get_runs())
        self.assertEqual(len(runs), 1)
        return runs

    def test_is_run_as_user(self):
        current_user = getuser()
        runs = self._make_configurator_and_runs()
        DebugExecutor, all_outputs, _ = make_executor_cls()

        ex = DebugExecutor(
            runs, False, self.ui, initials_and_capabilities=self._initial_settings
        )
        ex.execute()

        self.assertEqual(runs[0].get_number_of_data_points(), 2)
        self.assertEqual(len(all_outputs), 2)

        has_seen_benchmark_user = False
        for output in all_outputs:
            for line in output.splitlines():
                if line.startswith("Benchmark User:"):
                    has_seen_benchmark_user = True
                    self.assertEqual(line.split(":")[1].strip(), current_user)

        self.assertEqual(has_seen_benchmark_user, True)

    def test_has_the_env_variables(self):
        runs = self._make_configurator_and_runs()
        DebugExecutor, all_outputs, all_cmds = make_executor_cls()

        ex = DebugExecutor(
            runs, False, self.ui, initials_and_capabilities=self._initial_settings
        )
        ex.execute()

        self.assertEqual(runs[0].get_number_of_data_points(), 2)
        self.assertEqual(len(all_outputs), 2)

        expected = {
            "LUA_PATH": "?.lua;../../awfy/Lua/?.lua",
            "TEST": "just a string",
            "A_NUMBER": "42",
        }

        # also used in issue_42_vm.py
        known_envvars = [
            "PWD",
            "SHLVL",
            "VERSIONER_PYTHON_VERSION",
            "_",
            "__CF_USER_TEXT_ENCODING",
            "LC_CTYPE",
            "CPATH",
            "LIBRARY_PATH",
            "MANPATH",
            "SDKROOT",
        ]

        found_envvars = 0
        for output in all_outputs:
            for line in output.splitlines():
                if line.startswith("env:"):
                    env_var = line.split(":")[1].strip()
                    [name, value] = env_var.split("=")

                    # the env is sometimes polluted with other stuff
                    # let's just ignore that for now.
                    if name in known_envvars:
                        continue

                    assert (
                        name in expected
                    ), f"Unexpected env var: {name}. Output: {output}"
                    assert value == expected[name]
                    found_envvars += 1

        assert found_envvars == 3 * 2  # the *2 is because we run the benchmark twice

        cmd = all_cmds[0]
        self.assertIn(["env", "-i"], [cmd[i : i + 2] for i in range(len(cmd) - 1)])

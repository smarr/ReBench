from ..rebench_test_case import ReBenchTestCase

from ...persistence import DataStore
from ...configurator import Configurator, load_config
from ...executor import Executor


class Issue112Test(ReBenchTestCase):

    def setUp(self):
        super(Issue112Test, self).setUp()
        self._set_path(__file__)

    def test_invocation_setting_on_experiment(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, exp_name='ExpSetting', data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)

    def test_invocation_setting_on_experiment_execution_detail(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, exp_name='ExecSetting', data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 7, 7)

    def test_invocation_setting_for_global_run_details(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, exp_name='GlobalSetting', data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 5, 5)

    def test_invocation_setting_in_suite(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, exp_name='SuiteSetting', data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 3, 3)

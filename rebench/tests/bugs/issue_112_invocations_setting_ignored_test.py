from ..rebench_test_case import ReBenchTestCase

from ...persistence import DataStore
from ...configurator import Configurator, load_config
from ...executor import Executor


class Issue112Test(ReBenchTestCase):

    def setUp(self):
        super(Issue112Test, self).setUp()
        self._set_path(__file__)

    def test_iteration_invocation_semantics(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)
        self.assertTrue(False)


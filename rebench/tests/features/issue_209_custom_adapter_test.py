from ..rebench_test_case import ReBenchTestCase
from ...configurator import Configurator, load_config
from ...executor import Executor
from ...persistence import DataStore
from ...rebench import ReBench
from ..persistence import TestPersistence


class Issue209CustomAdapter(ReBenchTestCase):

    def setUp(self):
        super(Issue209CustomAdapter, self).setUp()
        self._set_path(__file__)
        self._data_store = DataStore(self.ui)
        self._cli_options = ReBench().shell_options().parse_args(['Exp1'])

    def test_custom_adapter_gives_data(self):
        raw_config = load_config(self._path + '/issue_209.conf')
        cnf = Configurator(raw_config,
                           self._data_store, self.ui, self._cli_options,
                           exp_name='Exp1', data_file=self._tmp_file)

        runs = cnf.get_runs()
        persistence = TestPersistence()
        persistence.use_on(runs)

        self.assertEqual(1, len(runs))

        # self._data_store.load_data(None, False)
        ex = Executor(cnf.get_runs(), True, self.ui, build_log=cnf.build_log,
                      config_dir=raw_config['__dir__'])
        self.assertTrue(ex.execute())

        data_points = persistence.get_data_points()
        self.assertEqual(1, len(data_points))
        self.assertEqual(1.1, data_points[0].get_total_value())

    def test_custom_adapters_are_not_confused_and_give_expected_data(self):
        raw_config = load_config(self._path + '/issue_209.conf')
        cnf = Configurator(raw_config,
                           self._data_store, self.ui, self._cli_options,
                           exp_name='Exp2', data_file=self._tmp_file)

        runs = cnf.get_runs()
        persistence = TestPersistence()
        persistence.use_on(runs)

        self.assertEqual(2, len(runs))

        # self._data_store.load_data(None, False)
        ex = Executor(cnf.get_runs(), True, self.ui, build_log=cnf.build_log,
                      config_dir=raw_config['__dir__'])
        self.assertTrue(ex.execute())

        data_points = persistence.get_data_points()
        data_points.sort(key=lambda x: x.get_total_value())

        self.assertEqual(2, len(data_points))
        self.assertEqual(2.1, data_points[0].get_total_value())
        self.assertEqual(3.1, data_points[1].get_total_value())

    def test_gauge_adapter_not_available(self):
        raw_config = load_config(self._path + '/issue_209.conf')
        cnf = Configurator(raw_config,
                           self._data_store, self.ui, self._cli_options,
                           exp_name='Exp3', data_file=self._tmp_file)

        runs = cnf.get_runs()
        persistence = TestPersistence()
        persistence.use_on(runs)

        self.assertEqual(1, len(runs))

        # self._data_store.load_data(None, False)
        ex = Executor(cnf.get_runs(), True, self.ui, build_log=cnf.build_log,
                      config_dir=raw_config['__dir__'])
        self.assertFalse(ex.execute())

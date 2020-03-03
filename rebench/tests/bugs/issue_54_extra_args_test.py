from ..rebench_test_case import ReBenchTestCase

from ...configurator import Configurator, load_config
from ...persistence  import DataStore


class Issue54Test(ReBenchTestCase):

    def setUp(self):
        super(Issue54Test, self).setUp()
        self._set_path(__file__)

    def test_expansion_of_extra_args(self):
        cnf = Configurator(load_config(self._path + '/issue_54.conf'),
                           DataStore(self._ui), self._ui, None, 'Test')

        runs = cnf.get_runs()
        self.assertEqual(1, len(runs))
        self.assertIn('INPUT_SIZE', list(runs)[0].cmdline())

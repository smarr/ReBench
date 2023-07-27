import os

from ..rebench_test_case import ReBenchTestCase
from ...executor          import Executor
from ...configurator      import Configurator, load_config
from ...persistence       import DataStore


class RetrieveIvocationTest(ReBenchTestCase):

    def setUp(self):
        super(RetrieveIvocationTest, self).setUp()
        os.chdir(self._path + '/../')

    def test_get_invocation_from_cmdline(self):
        cnf = Configurator(load_config(os.path.join(self._path,'features', 'issue_216.conf')),
                           DataStore(self.ui), self.ui, None,
                           data_file=self._tmp_file)
        runs = cnf.get_runs()
        ex = Executor(runs, cnf.do_builds, self.ui)
        ex.execute()
        cmdlines = [run_id.get_cmdline() for run_id in ex.runs]
        for cmd in cmdlines:
            sequence_numbers = [self.get_sequence_number(cmdline) for cmdline in cmd]
            is_increasing = self.is_list_increasing(sequence_numbers)
            self.assertTrue(is_increasing)

    def is_list_increasing(self,lst):
        return all(x < y for x, y in zip(lst, lst[1:]))

    def get_sequence_number(self,cmdline):
        last_element = cmdline.split()[-1]
        try:
            return int(last_element)
        except ValueError:
            return float('-inf')

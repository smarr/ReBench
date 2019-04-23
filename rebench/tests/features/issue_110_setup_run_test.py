# Copyright (c) 2019 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import os

from ..rebench_test_case import ReBenchTestCase

from ...configurator import Configurator, load_config
from ...executor import Executor
from ...persistence import DataStore
from ...rebench import ReBench


class Issue110Test(ReBenchTestCase):

    def _cleanup_file(self, file_name):
        if os.path.isfile(self._path + '/' + file_name):
            os.remove(self._path + '/' + file_name)

    def setUp(self):
        super(Issue110Test, self).setUp()
        self._set_path(__file__)
        self._cleanup_file('build.log')
        self._cleanup_file('rebench.data')
        self._data_store = DataStore(self._ui)
        self._cli_options = ReBench().shell_options().parse_args(['-d', '--setup-only', 'dummy'])

    def tearDown(self):
        self._cleanup_file('rebench.data')
        self._cleanup_file('build.log')
        self._cleanup_file('vm_110a.sh')
        self._cleanup_file('vm_110b.sh')

    def _read_log(self):
        file_name = 'build.log'
        file_path = self._path + '/' + file_name
        if os.path.isfile(file_path):
            with open(file_path, 'r') as log_file:
                lines = log_file.read().strip().split("\n")
                return set(lines)
        return None

    def _assert_runs(self, cnf, num_runs, num_dps, num_invocations):
        runs = cnf.get_runs()
        self.assertEqual(num_runs, len(runs), "incorrect number of runs")

        for run in runs:
            self.assertEqual(num_dps, run.get_number_of_data_points(),
                             "incorrect num of data points")
            self.assertEqual(num_invocations, run.completed_invocations,
                             "incorrect num of invocations")

    def _execute(self, cnf):
        ex = Executor(cnf.get_runs(), False, True, self._ui, build_log=cnf.build_log)
        ex.execute()

    def test_complete(self):
        cnf = Configurator(load_config(self._path + '/issue_110.conf'),
                           self._data_store, self._ui, self._cli_options,
                           exp_name='Complete', data_file=self._tmp_file)
        self._data_store.load_data(None, False)

        runs = cnf.get_runs()
        # depending on the ordering in the runs,
        # we may get 2 or 3 executions since SuiteWithBuild
        # uses one of the executors too
        self.assertTrue(len(runs) == 3 or len(runs) == 2)
        for run in runs:
            self.assertEqual(0, run.get_number_of_data_points(),
                             "incorrect num of data points")
            self.assertEqual(0, run.completed_invocations,
                             "incorrect num of invocations")

        self._execute(cnf)

        runs = cnf.get_runs()
        self.assertTrue(len(runs) == 3 or len(runs) == 2)

        for run in runs:
            self.assertEqual(1, run.get_number_of_data_points(),
                             "incorrect num of data points")
            self.assertEqual(1, run.completed_invocations,
                             "incorrect num of invocations")

        log = self._read_log()
        self.assertEqual({"E:BashB|STD:Built VM110B",
                          "E:BashA|STD:Built VM110A",
                          "S:SuiteWithBuild|STD:Built Suite"}, log)

    def test_a1(self):
        cnf = Configurator(load_config(self._path + '/issue_110.conf'),
                           self._data_store, self._ui, self._cli_options,
                           exp_name='A1', data_file=self._tmp_file)
        self._data_store.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        self._execute(cnf)

        self._assert_runs(cnf, 1, 1, 1)

        log = self._read_log()
        self.assertEqual({"E:BashA|STD:Built VM110A"}, log)

    def test_b2(self):
        cnf = Configurator(load_config(self._path + '/issue_110.conf'),
                           self._data_store, self._ui, self._cli_options,
                           exp_name='B2', data_file=self._tmp_file)
        self._data_store.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        self._execute(cnf)

        self._assert_runs(cnf, 1, 1, 1)

        log = self._read_log()
        self.assertEqual({"E:BashB|STD:Built VM110B"}, log)

    def test_suite_with_build(self):
        cnf = Configurator(load_config(self._path + '/issue_110.conf'),
                           self._data_store, self._ui, self._cli_options,
                           exp_name='SuiteWithBuild', data_file=self._tmp_file)
        self._data_store.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        self._execute(cnf)

        self._assert_runs(cnf, 1, 1, 1)

        log = self._read_log()
        self.assertEqual({"E:BashA|STD:Built VM110A",
                          "S:SuiteWithBuild|STD:Built Suite"}, log)

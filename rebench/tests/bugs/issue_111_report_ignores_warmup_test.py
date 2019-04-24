# Copyright (c) 2019 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from ..rebench_test_case import ReBenchTestCase

from ...configurator import Configurator, load_config
from ...executor import Executor
from ...persistence import DataStore


class Issue111Test(ReBenchTestCase):

    def setUp(self):
        super(Issue111Test, self).setUp()
        self._set_path(__file__)

    def test_invocation_and_mean_with_warmup_2(self):
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_111.conf'),
                           ds, self._ui, exp_name='test-warmup-2', data_file=self._tmp_file)
        runs = cnf.get_runs()
        ds.load_data(runs, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(runs, False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 7, 1)
        run = runs.pop()
        self.assertEqual(run.get_mean_of_totals(), 10)

        # Reload data from file, and confirm we get the same result
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_111.conf'),
                           ds, self._ui, exp_name='test-warmup-2', data_file=self._tmp_file)
        runs = cnf.get_runs()
        ds.load_data(runs, False)

        self._assert_runs(cnf, 1, 7, 1)
        run = runs.pop()
        self.assertEqual(run.get_mean_of_totals(), 10)

    def test_invocation_and_mean_with_warmup_0(self):
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_111.conf'),
                           ds, self._ui, exp_name='test-warmup-0', data_file=self._tmp_file)
        runs = cnf.get_runs()
        ds.load_data(runs, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(runs, False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 9, 1)
        run = runs.pop()
        self.assertEqual(run.get_mean_of_totals(), 230)

        # Reload data from file, and confirm we get the same result
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_111.conf'),
                           ds, self._ui, exp_name='test-warmup-0', data_file=self._tmp_file)
        runs = cnf.get_runs()
        ds.load_data(runs, False)

        self._assert_runs(cnf, 1, 9, 1)
        run = runs.pop()
        self.assertEqual(run.get_mean_of_totals(), 230)

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

from ...persistence import DataStore
from ...configurator import Configurator, load_config
from ...executor import Executor


class Issue112Test(ReBenchTestCase):

    def setUp(self):
        super(Issue112Test, self).setUp()
        self._set_path(__file__)

    def _test(self, exp_name, exp_result):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_112.conf'),
                           ds, self._ui, exp_name=exp_name, data_file=self._tmp_file)
        ds.load_data(None, False)

        # Has not executed yet, check that there is simply
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, exp_result, exp_result)

    def test_invocation_setting_on_experiment(self):
        self._test('ExpSetting', 10)

    def test_invocation_setting_on_experiment_execution_detail(self):
        self._test('ExecSetting', 7)

    def test_invocation_setting_for_global_run_details(self):
        self._test('GlobalSetting', 5)

    def test_invocation_setting_in_suite(self):
        self._test('SuiteSetting', 3)

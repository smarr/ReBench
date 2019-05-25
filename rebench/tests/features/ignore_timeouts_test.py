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


class IgnoreTimeoutsTest(ReBenchTestCase):

    def setUp(self):
        super(IgnoreTimeoutsTest, self).setUp()
        self._set_path(__file__)

    def _init(self, exp_name):
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/ignore_timeouts.conf'),
                           ds, self._ui, exp_name=exp_name, data_file=self._tmp_file)
        ds.load_data(None, False)
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.cmdline())
        return ds, cnf, runs

    def test_ignore_timeouts_globally(self):
        # test that the flag is set correctly on the runs
        _, _, runs = self._init('GlobalSettings')

        self.assertTrue(runs[0].ignore_timeouts)
        self.assertFalse(runs[1].ignore_timeouts)
        self.assertTrue(runs[2].ignore_timeouts)
        self.assertTrue(runs[3].ignore_timeouts)
        self.assertFalse(runs[4].ignore_timeouts)
        self.assertTrue(runs[5].ignore_timeouts)
        self.assertFalse(runs[6].ignore_timeouts)
        self.assertFalse(runs[7].ignore_timeouts)
        self.assertTrue(runs[8].ignore_timeouts)

    def test_ignore_timeouts_accepts_data_after_timeout_and_does_not_cause_warnings(self):
        _, cnf, runs = self._init('Exec')
        self.assertEqual(1, len(runs))

        ex = Executor(runs, False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 1)
        self.assertFalse(runs[0].run_failed())

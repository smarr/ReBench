# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
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
from ...configurator           import Configurator, load_config
from ...executor               import Executor
from ...persistence            import DataStore
from ...ui                     import TestDummyUI

from ..rebench_test_case import ReBenchTestCase


class Issue15WarmUpSupportTest(ReBenchTestCase):
    """
      - a configuration to define the number of warm-up runs
      - a template parameter for the command
      - ignore measurements for those runs
        (let's ignore situations were the harness supports warm-up)
    """

    def setUp(self):
        super(Issue15WarmUpSupportTest, self).setUp()
        self._set_path(__file__)

    def test_run_id_indicates_warm_up_iterations_required(self):
        cnf = Configurator(load_config(self._path + '/issue_15.conf'), DataStore(self._ui),
                           self._ui, data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertGreaterEqual(len(runs), 1)

        self.assertTrue(runs[0].requires_warmup())
        self.assertGreater(runs[0].warmup_iterations, 0)

    def test_warm_up_results_should_be_ignored(self):
        cnf = Configurator(load_config(self._path + '/issue_15.conf'), DataStore(self._ui),
                           self._ui, data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertEqual(runs[0].get_number_of_data_points(), 0)
        self.assertEqual(runs[0].warmup_iterations, 13)

        ex = Executor([runs[0]], False, False, TestDummyUI())
        ex.execute()

        self.assertEqual(runs[0].get_number_of_data_points(), 10)

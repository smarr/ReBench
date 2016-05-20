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
from ...configurator           import Configurator
from ...executor               import Executor
from ...persistence            import DataStore

from ..rebench_test_case import ReBenchTestCase


class Issue15WarmUpSupportTest(ReBenchTestCase):
    """
      - a configuration to define the number of warm-up runs
      - a template parameter for the command
      - ignore measurements for those runs
        (let's ignore situations were the harness supports warm-up)
    """

    def setUp(self):
        super(Issue15WarmUpSupportTest, self).setUp(__file__)

    def test_run_id_indicates_warm_up_iterations_required(self):
        cnf = Configurator(self._path + '/issue_15.conf', DataStore(),
                           standard_data_file = self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertGreaterEqual(len(runs), 1)

        self.assertTrue(runs[0].requires_warmup())
        self.assertGreater(runs[0].warmup_iterations, 0)

    def test_warm_up_results_should_be_ignored(self):
        cnf = Configurator(self._path + '/issue_15.conf', DataStore(),
                           standard_data_file = self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertEquals(runs[0].get_number_of_data_points(), 0)
        self.assertEquals(runs[0].warmup_iterations, 13)

        ex = Executor([runs[0]], False)
        ex.execute()

        self.assertEquals(runs[0].get_number_of_data_points(),
                          runs[0].run_config.number_of_data_points)
        self.assertLessEqual(runs[0].get_total_values()[0], 850)

# Copyright (c) 2017 Stefan Marr <http://www.stefan-marr.de/>
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
from ...configurator     import Configurator, load_config
from ...executor         import Executor
from ...persistence      import DataStore
from ..rebench_test_case import ReBenchTestCase


class Issue57ExecutableOnPath(ReBenchTestCase):

    def setUp(self):
        super(Issue57ExecutableOnPath, self).setUp()
        self._set_path(__file__)

    def test_sleep_gives_results(self):
        store = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/issue_57.conf'), store,
                           self._ui, data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, False, False, self._ui, False)
        ex.execute()

        self.assertEqual("Bench1", runs[0].benchmark.name)
        self.assertEqual(10, runs[0].get_number_of_data_points())

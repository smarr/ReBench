# Copyright (c) 2023 Naomi Grew, Stefan Marr
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
from ..persistence import TestPersistence
from ..rebench_test_case import ReBenchTestCase


class Issue216CurrentInvocation(ReBenchTestCase):

    def setUp(self):
        super(Issue216CurrentInvocation, self).setUp()
        self._set_path(__file__)

    def _records_data_points(self, exp_name, num_data_points):
        cnf = Configurator(load_config(self._path + '/issue_216.conf'), DataStore(self.ui),
                           self.ui, exp_name=exp_name,
                           data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertEqual(1, len(runs))

        persistence = TestPersistence()
        persistence.use_on(runs)
        ex = Executor(runs, False, self.ui)
        ex.execute()

        run = runs[0]
        self.assertEqual(num_data_points, run.get_number_of_data_points())
        return persistence.get_data_points()

    def test_associates_measurements_and_data_points_correctly(self):
        data_points = self._records_data_points('Test', 4)
        for point, i in zip(data_points, range(4)):
            self.assertEqual(1, len(point.get_measurements()))
            self.assertEqual(i + 1, int(point.get_measurements()[0].value))

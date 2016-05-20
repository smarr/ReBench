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


class Issue16MultipleDataPointsTest(ReBenchTestCase):
    """
    Add support to record multiple data points for same benchmark in one run.
      - multiple measurements
      - as well as multiple data points
    """

    def setUp(self):
        super(Issue16MultipleDataPointsTest, self).setUp(__file__)

    def _records_data_points(self, exp_name, num_data_points):
        cnf = Configurator(self._path + '/issue_16.conf', DataStore(),
                           exp_name=exp_name,
                           standard_data_file=self._tmp_file)
        ex = Executor(cnf.get_runs(), False)
        ex.execute()
        self.assertEquals(1, len(cnf.get_runs()))
        run = iter(cnf.get_runs()).next()
        self.assertEquals(num_data_points, len(run.get_data_points()))
        return run.get_data_points()

    def test_records_multiple_data_points_from_single_execution_10(self):
        self._records_data_points('Test1', 10)

    def test_records_multiple_data_points_from_single_execution_20(self):
        self._records_data_points('Test2', 20)

    def test_associates_measurements_and_data_points_correctly(self):
        data_points = self._records_data_points('Test1', 10)
        for dp, i in zip(data_points, range(0, 10)):
            self.assertEquals(4, dp.number_of_measurements())

            for criterion, measurement in zip(["bar", "baz", "foo", "total"],
                                              dp.get_measurements()):
                self.assertEquals(criterion, measurement.criterion)
                self.assertEquals(i,         int(measurement.value))

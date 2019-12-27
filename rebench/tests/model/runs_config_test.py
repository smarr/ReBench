# Copyright (c) 2016 Stefan Marr <http://www.stefan-marr.de/>
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
from ...model.data_point import DataPoint
from ...model.measurement import Measurement
from ...model.termination_check import TerminationCheck
from ...configurator import Configurator, load_config
from ...persistence  import DataStore
from ..rebench_test_case import ReBenchTestCase


class RunsConfigTestCase(ReBenchTestCase):

    def setUp(self):
        super(RunsConfigTestCase, self).setUp()
        self._cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                                 self._ui, None,
                                 data_file=self._tmp_file)
        runs = self._cnf.get_runs()
        self._run = list(runs)[0]

    def test_termination_check_basic(self):
        check = TerminationCheck(self._run, self._ui)
        self.assertFalse(check.should_terminate(0, None))

        # start 9 times, but expect to be done only after 10
        for i in range(1, 10):
            dp = DataPoint(self._run)
            dp.add_measurement(Measurement(i, 1, 0, 'ms', self._run))
            self._run.loaded_data_point(dp, False)
        self.assertFalse(check.should_terminate(0, None))

        dp = DataPoint(self._run)
        dp.add_measurement(Measurement(10, 1, 0, 'ms', self._run))
        self._run.loaded_data_point(dp, False)
        self.assertTrue(check.should_terminate(0, None))

    def test_terminate_not_determine_by_number_of_data_points(self):
        check = TerminationCheck(self._run, self._ui)
        self.assertFalse(check.should_terminate(0, None))
        self.assertFalse(check.should_terminate(10, None))
        self.assertFalse(check.should_terminate(10000, None))

    def test_consecutive_fails(self):
        check = TerminationCheck(self._run, self._ui)
        self.assertFalse(check.should_terminate(0, None))

        for _ in range(0, 2):
            check.indicate_failed_execution()
            self.assertFalse(check.should_terminate(0, None))

        check.indicate_failed_execution()
        self.assertTrue(check.should_terminate(0, None))

    def test_too_many_fails(self):
        check = TerminationCheck(self._run, self._ui)
        self.assertFalse(check.should_terminate(0, None))

        for _ in range(0, 6):
            check.indicate_failed_execution()
            check.indicate_successful_execution()
            self.assertFalse(check.should_terminate(0, None))

        check.indicate_failed_execution()
        self.assertTrue(check.should_terminate(0, None))

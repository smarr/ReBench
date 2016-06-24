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
from ...configurator     import Configurator
from ...executor         import Executor, RoundRobinScheduler
from ...persistence      import DataStore
from ...reporter         import Reporter
from ..rebench_test_case import ReBenchTestCase


class TestReporter(Reporter):

    def __init__(self, test_case):
        self._test_case = test_case

    def run_failed(self, run_id, cmdline, return_code, output):
        self._test_case.fail()

    def run_completed(self, run_id, statistics, cmdline):
        self._test_case.run_completed(run_id)

    def job_completed(self, run_ids):
        pass

    def set_total_number_of_runs(self, num_runs):
        pass

    def start_run(self, run_id):
        self._test_case.start_run(run_id)


class Issue19OneDataPointAtATime(ReBenchTestCase):
    """
    With large benchmark suites it can take hours to go through all runs,
    and it would be nice to get early feedback and allow the results to get
    refined with more measurements later on.
    """

    def setUp(self):
        super(Issue19OneDataPointAtATime, self).setUp(__file__)


class OneMeasurementAtATime(Issue19OneDataPointAtATime):

    def __init__(self, method_name = 'runTest'):
        super(OneMeasurementAtATime, self).__init__(method_name)
        self._run_id = None
        self._run_count = {}

    def run_completed(self, run_id):
        print "completed", run_id
        self.assertIs(self._run_id, run_id)

    def start_run(self, run_id):
        """ Make sure that we do not do the same run twice in a row. """
        print "start", run_id
        self.assertIsNot(self._run_id, run_id)
        self._run_id = run_id
        self._run_count[run_id] = self._run_count.get(run_id, 0) + 1

    def test_one_measurement_at_a_time_and_correct_number_of_data_points(self):
        cnf = Configurator(self._path + '/issue_19.conf', DataStore(),
                           standard_data_file=self._tmp_file)
        reporter = TestReporter(self)
        for run in cnf.get_runs():
            run.add_reporter(reporter)

        ex = Executor(cnf.get_runs(), False, False, False, RoundRobinScheduler)
        ex.execute()

        for run in cnf.get_runs():
            self.assertEquals(10, run.get_number_of_data_points())
            self.assertEquals(10, self._run_count[run])

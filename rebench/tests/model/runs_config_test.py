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
from ...model.runs_config import TerminationCheck, QuickTerminationCheck
from ...configurator import Configurator
from ...persistence  import DataStore
from ..rebench_test_case import ReBenchTestCase


class RunsConfigTestCase(ReBenchTestCase):

    def setUp(self):
        super(RunsConfigTestCase, self).setUp()
        self._cnf = Configurator(self._path + '/small.conf', DataStore(), None,
                                 standard_data_file=self._tmp_file)
        runs = self._cnf.get_runs()
        self._run = list(runs)[0]

    def test_termination_check_basic(self):
        tc = TerminationCheck(self._run.run_config, self._run.bench_cfg)
        self.assertFalse(tc.should_terminate(0))
        self.assertTrue(tc.should_terminate(10))

    def test_consecutive_fails(self):
        tc = TerminationCheck(self._run.run_config, self._run.bench_cfg)
        self.assertFalse(tc.should_terminate(0))

        for i in range(0, 2):
            tc.indicate_failed_execution()
            self.assertFalse(tc.should_terminate(0))

        tc.indicate_failed_execution()
        self.assertTrue(tc.should_terminate(0))

    def test_too_many_fails(self):
        tc = TerminationCheck(self._run.run_config, self._run.bench_cfg)
        self.assertFalse(tc.should_terminate(0))

        for i in range(0, 6):
            tc.indicate_failed_execution()
            tc.indicate_successful_execution()
            self.assertFalse(tc.should_terminate(0))

        tc.indicate_failed_execution()
        self.assertTrue(tc.should_terminate(0))

    def test_quick_termination(self):
        tc = QuickTerminationCheck(self._run.run_config, self._run.bench_cfg)
        self._run.run_config.max_time = -1
        self.assertTrue(tc.should_terminate(0))

        self._run.run_config.max_time = 100000000000
        self.assertFalse(tc.should_terminate(0))

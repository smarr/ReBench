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
import unittest
import subprocess

from ..executor          import Executor, BenchmarkThreadExceptions
from ..configurator      import Configurator
from ..model.measurement import Measurement
from ..persistence       import DataStore
from ..                  import ReBench
import os
import sys
from .rebench_test_case import ReBenchTestCase


class ExecutorTest(ReBenchTestCase):
    
    def setUp(self):
        super(ExecutorTest, self).setUp(__file__)
        os.chdir(self._path + '/../')

    def test_setup_and_run_benchmark(self):
        # before executing the benchmark, we override stuff in subprocess for testing
        subprocess.Popen =  Popen_override
        options = ReBench().shell_options().parse_args([])[0]
        
        cnf  = Configurator(self._path + '/test.conf', DataStore(), options,
                            None, 'Test', standard_data_file = self._tmp_file)
        
        ex = Executor(cnf.get_runs(), cnf.use_nice)
        ex.execute()
        
### should test more details
#        (mean, sdev, (interval, interval_percentage), 
#                (interval_t, interval_percentage_t)) = ex.result['test-vm']['test-bench']
#        
#        self.assertEqual(31, len(ex.benchmark_data['test-vm']['test-bench']))
#        self.assertAlmostEqual(45870.4193548, mean)
#        self.assertAlmostEqual(2.93778711485, sdev)
#        
#        (i_low, i_high) = interval
#        self.assertAlmostEqual(45869.385195243565, i_low)
#        self.assertAlmostEqual(45871.453514433859, i_high)
#        self.assertAlmostEqual(0.00450904792104, interval_percentage)

    def test_broken_command_format(self):
        def test_exit(val):
            self.assertEquals(-1, val, "got the correct error code")
            raise RuntimeError("TEST-PASSED")
        sys.exit = test_exit

        try:
            options = ReBench().shell_options().parse_args([])[0]
            cnf = Configurator(self._path + '/test.conf', DataStore(), options,
                               None, 'TestBrokenCommandFormat',
                               standard_data_file=self._tmp_file)
            ex = Executor(cnf.get_runs(), cnf.use_nice)
            ex.execute()
        except RuntimeError as e:
            self.assertEqual("TEST-PASSED", e.message)
        except BenchmarkThreadExceptions as e:
            self.assertEqual("TEST-PASSED", e.exceptions[0].message)
    
    def test_broken_command_format_with_TypeError(self):
        def test_exit(val):
            self.assertEquals(-1, val, "got the correct error code")
            raise RuntimeError("TEST-PASSED")
        sys.exit = test_exit
        
        try:
            options = ReBench().shell_options().parse_args([])[0]
            cnf = Configurator(self._path + '/test.conf', DataStore(), options,
                               None, 'TestBrokenCommandFormat2',
                               standard_data_file=self._tmp_file)
            ex = Executor(cnf.get_runs(), cnf.use_nice)
            ex.execute()
        except RuntimeError as e:
            self.assertEqual("TEST-PASSED", e.message)
        except BenchmarkThreadExceptions as e:
            self.assertEqual("TEST-PASSED", e.exceptions[0].message)

    def _basic_execution(self, cnf):
        runs = cnf.get_runs()
        self.assertEquals(8, len(runs))
        ex = Executor(cnf.get_runs(), cnf.use_nice)
        ex.execute()
        for run in runs:
            data_points = run.get_data_points()
            self.assertEquals(10, len(data_points))
            for data_point in data_points:
                measurements = data_point.get_measurements()
                self.assertEquals(4, len(measurements))
                self.assertIsInstance(measurements[0], Measurement)
                self.assertTrue(measurements[3].is_total())
                self.assertEquals(data_point.get_total_value(),
                                  measurements[3].value)

    def test_basic_execution(self):
        cnf = Configurator(self._path + '/small.conf', DataStore(), None,
                           standard_data_file = self._tmp_file)
        self._basic_execution(cnf)

    def test_basic_execution_with_magic_all(self):
        cnf = Configurator(self._path + '/small.conf', DataStore(), None, None,
                           'all', standard_data_file = self._tmp_file)
        self._basic_execution(cnf)
        

def Popen_override(cmdline, stdout, stderr=None, shell=None):
    class Popen:
        returncode = 0
        def communicate(self):
            return "", ""
        def poll(self):
            return self.returncode
    
    return Popen()


def test_suite():
    return unittest.makeSuite(ExecutorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')

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
import tempfile
import os

from ..performance import CaliperPerformance
from ..persistence import DataPointPersistence
from .. import ReBench
from ..configurator import Configurator
from ..executor import Executor


class CaliperIntegrationTest(unittest.TestCase):
    """CaliperTest verifies the proper support for the
       ReBenchConsoleResultProcessor output produced by
       the Caliper version hosted at:
         
         https://github.com/smarr/caliper
    
       The test relies on pre-generated example data, but
       covers the whole process of benchmarking, including
       execution, and result parsing.
    """ 

    def setUp(self):
        self._tmpFile = tempfile.mkstemp()[1] # just use the file name
        
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._cwd  = os.getcwd()
        os.chdir(self._path + '/../')

    def tearDown(self):
        os.remove(self._tmpFile)
        os.chdir(self._cwd)

    # Integration Test
    def test_full_execution(self):
        ## assert for the expected measurements as results
        ## test for the expected number of executions of the
        ## caliper runner
        options = ReBench().shell_options().parse_args([])[0]
        
        cnf  = Configurator(self._path + '/test.conf', options, 'TestCaliper')
        data = DataPointPersistence.get(self._tmpFile, True)
        
        ex = Executor(cnf.get_runs(), False, Reporters([]))
        ex.execute()
    
    def test_correct_number_of_results_from_run(self):
        # TODO:
        ## Make sure that ReBench understands that a single
        ## execution can return multiple results
        ## Normally that should already be there...

        pass


class CaliperPerformanceReaderTest(unittest.TestCase):
    """ test the parser for correctly understanding the
        caliper output
    """
    
    def setUp(self):
        self._result1 = "Measurement (runtime) for SimpleExecution in AliasMOP.ExampleBench: 52.316778ns"
        self._result2 = "Measurement (runtime) for SimpleAdditionAmbientTalk in AliasMOP.ExampleBench: 17365.513556ns"
        self._c       = CaliperPerformance()
        self._path    = os.path.dirname(os.path.realpath(__file__))
    
    def test_unmodified_command(self):
        
        cmd = ""
        self.assertEqual(cmd, self._c.acquire_command(cmd))
        
        cmd = "foobar"
        self.assertEqual(cmd, self._c.acquire_command(cmd))
        
        cmd = "  foo barr  "
        self.assertEqual(cmd, self._c.acquire_command(cmd))

    @unittest.skip("Test needs to be adapted to new ReBench version")
    def test_parse_single_result(self):
        parsed = self._c.parse_data(self._result1, None)
        self.assertAlmostEqual(0.000052316778, parsed[0].get_total_value())

        measurement = parsed[0].get_measurements()[0]
        self.assertEqual("SimpleExecution", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)
        
        measurement = parsed[1][1] # a fake result for the totals
        self.assertEqual("total", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)
        
        parsed = self._c.parse_data(self._result2, None)
        self.assertIsProperTupleWithTotal(0.017365513556, parsed)
        measurement = parsed[1][0]
        self.assertEqual("SimpleAdditionAmbientTalk", measurement.criterion)
        self.assertAlmostEqual(0.017365513556, measurement.value)
        
        measurement = parsed[1][1] # a fake result for the totals
        self.assertEqual("total", measurement.criterion)
        self.assertAlmostEqual(0.017365513556, measurement.value)

    @unittest.skip("Test needs to be adapted to new ReBench version")
    def test_parse_multiple_results1(self):
        parsed = self._c.parse_data((self._result1 + "\n") * 10, None)
        self.assertAlmostEqual(0.000052316778, parsed[0].get_total_value())
        self.assertEquals(10, len(parsed))

        # TODO
        self.assertEqual(20, len(parsed[1].get_measurements()))
        measurement = parsed[1].get_measurements()[0]
        self.assertEqual("SimpleExecution", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)
        
        measurement = parsed[1][1] # this is a fake result for the totals
        self.assertEqual("total", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)
        
        measurement = parsed[1][4]
        self.assertEqual("SimpleExecution", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)
        
        measurement = parsed[1][5] # another fake result
        self.assertEqual("total", measurement.criterion)
        self.assertEqual(0.000052316778, measurement.value)

    @unittest.skip("Test needs to be adapted to new ReBench version")
    def test_parse_caliper_output_bug1(self):
        with open (self._path + '/caliper-bug1.output', "r") as f:
            data = f.read()
        
        parsed = self._c.parse_data(data, None)
        self.assertEquals(1, len(parsed))
        self.assertAlmostEqual(4.507679245283001, parsed[0].get_total_value())
    
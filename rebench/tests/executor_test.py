import unittest
import subprocess

from ..Executor       import Executor
from ..DataAggregator import DataAggregator
from ..Configurator   import Configurator
from ..Reporter       import Reporters
from ..model.benchmark_config import BenchmarkConfig
from rebench          import ReBench
import tempfile
import os
import sys

class ExecutorTest(unittest.TestCase):
    
    def setUp(self):
        BenchmarkConfig.reset()
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._tmpFile = tempfile.mkstemp()[1] # just use the file name
        os.chdir(self._path + '/../')
        
        self._sys_exit = sys.exit  # make sure that we restore sys.exit   
    
    def tearDown(self):
        os.remove(self._tmpFile)
        sys.exit = self._sys_exit
        
        
    def test_setup_and_run_benchmark(self):

        # before executing the benchmark, we override stuff in subprocess for testing
        subprocess.Popen =  Popen_override
        options = ReBench().shell_options().parse_args([])[0]
        
        cnf  = Configurator(self._path + '/test.conf', options, 'Test')
        data = DataAggregator(self._tmpFile)
        
        ex = Executor(cnf, data, Reporters([]))
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
        
        options = ReBench().shell_options().parse_args([])[0]
        cnf = Configurator(self._path + '/test.conf', options, 'TestBrokenCommandFormat')
        data = DataAggregator(self._tmpFile)
        ex = Executor(cnf, data, Reporters([]))
        
        with self.assertRaisesRegexp(RuntimeError, "TEST-PASSED"):
            ex.execute()
    
    def test_broken_command_format_with_TypeError(self):
        def test_exit(val):
            self.assertEquals(-1, val, "got the correct error code")
            raise RuntimeError("TEST-PASSED")
        sys.exit = test_exit
        
        options = ReBench().shell_options().parse_args([])[0]
        cnf = Configurator(self._path + '/test.conf', options, 'TestBrokenCommandFormat2')
        data = DataAggregator(self._tmpFile)
        ex = Executor(cnf, data, Reporters([]))
        
        with self.assertRaisesRegexp(RuntimeError, "TEST-PASSED"):
            ex.execute()

def Popen_override(cmdline, stdout, shell):
    class Popen:
        returncode = 0
        def communicate(self):
            return (None, None)
    
    return Popen()

def test_suite():
    return unittest.makeSuite(ExecutorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')